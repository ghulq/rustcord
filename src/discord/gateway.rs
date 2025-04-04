use super::{errors::DiscordError, util};
use futures::{SinkExt, StreamExt};
use pyo3::{prelude::*, types::PyDict};
use rand::Rng;
use serde::Deserialize;
use serde_json::{Value, json};
use std::{
    collections::HashMap,
    sync::{Arc, Mutex as StdMutex},
    time::{Duration, Instant},
};
use tokio::{
    runtime::Runtime,
    sync::{
        Mutex,
        mpsc::{self, Receiver, Sender},
    },
    time::interval,
};
use tokio_tungstenite::{connect_async, tungstenite::protocol::Message as WsMessage};
use url::Url;

// Gateway operation codes from Discord API
const GATEWAY_OP_DISPATCH: u8 = 0;
const GATEWAY_OP_HEARTBEAT: u8 = 1;
const GATEWAY_OP_IDENTIFY: u8 = 2;
const GATEWAY_OP_RESUME: u8 = 6;
const GATEWAY_OP_RECONNECT: u8 = 7;
const GATEWAY_OP_INVALID_SESSION: u8 = 9;
const GATEWAY_OP_HELLO: u8 = 10;
const GATEWAY_OP_HEARTBEAT_ACK: u8 = 11;

#[derive(Deserialize)]
pub(crate) struct GatewayData {
    #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
    pub(crate) url: Option<String>,
}

struct SharedGatewayClient {
    token: String,
    runtime: Runtime,
    last_heartbeat_ack: Mutex<Instant>,
    session_id: Mutex<Option<String>>,
    sequence: Mutex<Option<u64>>,
    event_callbacks: StdMutex<HashMap<String, PyObject>>,
    heartbeat_interval: Mutex<Option<u64>>,
}

impl SharedGatewayClient {
    fn new(token: String, runtime: Runtime) -> Self {
        Self {
            token,
            runtime,
            last_heartbeat_ack: Mutex::new(Instant::now()),
            session_id: Mutex::default(),
            sequence: Mutex::default(),
            event_callbacks: StdMutex::default(),
            heartbeat_interval: Mutex::default(),
        }
    }
}

/// Client for Discord Gateway WebSocket connections
#[pyclass]
pub struct GatewayClient {
    shared: Arc<SharedGatewayClient>,
    message_tx: Option<Sender<Value>>,
    intents: u32,
}

#[pymethods]
impl GatewayClient {
    /// Creates a new GatewayClient with the given token and intents
    #[new]
    pub fn new(token: String, intents: u32) -> PyResult<Self> {
        // Create a Tokio runtime for async operations
        let runtime =
            Runtime::new().map_err(|e| DiscordError::RuntimeError(e.to_string()).to_pyerr())?;

        Ok(Self {
            shared: Arc::new(SharedGatewayClient::new(token, runtime)),
            message_tx: None,
            intents,
        })
    }

    /// Register a callback for a specific gateway event
    pub fn on(&self, event_name: String, callback: PyObject) -> PyResult<()> {
        let mut callbacks = self
            .shared
            .event_callbacks
            .lock()
            .map_err(|e| DiscordError::MutexError(e.to_string()).to_pyerr())?;

        callbacks.insert(event_name, callback);
        Ok(())
    }

    /// Connect to the Discord Gateway
    pub fn connect(&mut self, gateway_url: String) -> PyResult<()> {
        self.connect_inner(gateway_url, None, None)
    }

    /// Connect to the Discord Gateway with sharding
    pub fn connect_sharded(
        &mut self,
        gateway_url: String,
        shard_id: usize,
        shard_count: usize,
    ) -> PyResult<()> {
        self.connect_inner(gateway_url, Some(shard_id), Some(shard_count))
    }

    fn connect_inner(
        &mut self,
        gateway_url: String,
        shard_id: Option<usize>,
        shard_count: Option<usize>,
    ) -> PyResult<()> {
        Python::with_gil(|_py| {
            let (message_tx, message_rx) = mpsc::channel(100);
            self.message_tx = Some(message_tx);

            let shared_cloned = self.shared.clone();
            let intents = self.intents;

            println!("Connecting with sharding: shard {shard_id:?}/{shard_count:?}");

            // Start the WebSocket connection in a background task
            self.shared.runtime.spawn(async move {
                if let Err(e) = gateway_connect(
                    gateway_url,
                    intents,
                    shard_id,
                    shard_count,
                    shared_cloned,
                    message_rx,
                )
                .await
                {
                    eprintln!(
                        "Gateway connection error for shard {shard_id:?}/{shard_count:?}: {e}"
                    );
                }
            });

            Ok(())
        })
    }

    /// Send a message through the gateway connection
    pub fn send(&self, data: &PyDict) -> PyResult<()> {
        if let Some(tx) = &self.message_tx {
            // Convert PyDict to JSON Value
            let json_data = Python::with_gil(|_| -> PyResult<Value> {
                let json_str = data.str()?.to_str()?;
                serde_json::from_str(json_str).map_err(|e| {
                    DiscordError::ParseError(format!("Failed to convert dict to JSON: {e}"))
                        .to_pyerr()
                })
            })?;

            let tx_clone = tx.clone();
            self.shared.runtime.spawn(async move {
                if let Err(e) = tx_clone.send(json_data).await {
                    eprintln!("Failed to send message to gateway: {e}");
                }
            });
        } else {
            return Err(DiscordError::NotConnected("Gateway not connected".to_string()).to_pyerr());
        }

        Ok(())
    }

    /// Disconnect from the gateway
    pub fn disconnect(&mut self) {
        self.message_tx = None;
    }
}

async fn gateway_connect(
    mut gateway_url: String,
    intents: u32,
    shard_id: Option<usize>,
    shard_count: Option<usize>,
    shared: Arc<SharedGatewayClient>,
    mut message_rx: Receiver<Value>,
) -> Result<(), DiscordError> {
    // Ensure the URL has the necessary parameters
    if !gateway_url.contains('?') {
        gateway_url.push_str("?v=10&encoding=json");
    }

    let gateway_url = Url::parse(&gateway_url)
        .map_err(|e| DiscordError::ParseError(format!("Invalid gateway URL: {e}")))?;

    let (ws_stream, _) = connect_async(gateway_url)
        .await
        .map_err(|e| DiscordError::ConnectionError(format!("WebSocket connection failed: {e}")))?;

    println!("Connected to Discord Gateway");

    // Split the WebSocket stream
    let (ws_sender, mut ws_receiver) = ws_stream.split();

    // Create a shared sender wrapped in thread-safe containers
    let ws_sender = Arc::new(Mutex::new(ws_sender));

    // Start heartbeat task when we receive the HELLO message
    let (heartbeat_tx, heartbeat_rx) = mpsc::channel::<bool>(1);

    // Clone variables for first task
    let ws_sender_clone1 = ws_sender.clone();
    let shared_cloned = shared.clone();

    // Handle incoming Gateway messages
    tokio::spawn(async move {
        process_gateway_messages(
            &mut ws_receiver,
            intents,
            ws_sender_clone1,
            shared_cloned,
            heartbeat_tx,
            shard_id,
            shard_count,
        )
        .await;
    });

    // Clone variables for heartbeat task
    let ws_sender_clone2 = ws_sender.clone();
    let shared_cloned2 = shared.clone();

    // Start heartbeat task
    tokio::spawn(async move {
        handle_heartbeats(heartbeat_rx, ws_sender_clone2, shared_cloned2).await;
    });

    // Forward outgoing messages from the channel to the WebSocket
    while let Some(message) = message_rx.recv().await {
        let message_text = match serde_json::to_string(&message) {
            Ok(text) => text,
            Err(e) => {
                eprintln!("Failed to serialize message: {e}");
                continue;
            }
        };

        {
            let mut ws_sender_guard = ws_sender.lock().await;
            if let Err(e) = ws_sender_guard.send(WsMessage::Text(message_text)).await {
                eprintln!("Failed to send message to gateway: {e}");
                break;
            }
        }
    }

    Ok(())
}

async fn process_gateway_messages(
    ws_receiver: &mut futures::stream::SplitStream<
        tokio_tungstenite::WebSocketStream<
            tokio_tungstenite::MaybeTlsStream<tokio::net::TcpStream>,
        >,
    >,
    intents: u32,
    ws_sender: Arc<
        Mutex<
            futures::stream::SplitSink<
                tokio_tungstenite::WebSocketStream<
                    tokio_tungstenite::MaybeTlsStream<tokio::net::TcpStream>,
                >,
                WsMessage,
            >,
        >,
    >,
    shared: Arc<SharedGatewayClient>,
    heartbeat_tx: mpsc::Sender<bool>,
    shard_id: Option<usize>,
    shard_count: Option<usize>,
) {
    while let Some(msg) = ws_receiver.next().await {
        match msg {
            Ok(WsMessage::Text(text)) => {
                // Parse the JSON message
                let data: Value = match serde_json::from_str(&text) {
                    Ok(data) => data,
                    Err(e) => {
                        eprintln!("Failed to parse gateway message: {e}");
                        continue;
                    }
                };

                // Extract operation code
                let op = data["op"].as_u64().unwrap_or(99);

                match op as u8 {
                    GATEWAY_OP_HELLO => {
                        // Extract heartbeat interval and start heartbeat task
                        if let Some(interval_ms) = data["d"]["heartbeat_interval"].as_u64() {
                            let mut interval_guard = shared.heartbeat_interval.lock().await;
                            *interval_guard = Some(interval_ms);
                            heartbeat_tx.send(true).await.ok();

                            // Send IDENTIFY to authenticate
                            let resume_possible = {
                                let sid = shared.session_id.lock().await;
                                let seq = shared.sequence.lock().await;
                                sid.is_some() && seq.is_some()
                            };

                            let identify = if resume_possible {
                                let sid = shared.session_id.lock().await.clone().unwrap();
                                let seq = shared.sequence.lock().await.unwrap();

                                json!({
                                    "op": GATEWAY_OP_RESUME,
                                    "d": {
                                        "token": shared.token,
                                        "session_id": sid,
                                        "seq": seq
                                    }
                                })
                            } else {
                                let mut json = json!({
                                    "op": GATEWAY_OP_IDENTIFY,
                                    "d": {
                                        "token": shared.token,
                                        "intents": intents,
                                        "properties": {
                                            "$os": std::env::consts::OS,
                                            "$browser": "rustcord",
                                            "$device": "rustcord"
                                        }
                                    }
                                });

                                // Check if we're using sharding
                                if let (Some(shard_id), Some(shard_count)) = (shard_id, shard_count)
                                {
                                    println!(
                                        "Sending IDENTIFY with shard [{shard_id}]/[{shard_count}]"
                                    );

                                    json["d"]["shard"] = json!([shard_id, shard_count]);
                                }

                                json
                            };

                            let identify_msg = WsMessage::Text(identify.to_string());

                            // Using scoped block to ensure MutexGuard is dropped before await
                            {
                                let mut ws_sender_guard = ws_sender.lock().await;
                                if let Err(e) = ws_sender_guard.send(identify_msg).await {
                                    eprintln!("Failed to send IDENTIFY: {e}");
                                }
                            }
                        }
                    }
                    GATEWAY_OP_DISPATCH => {
                        // Handle sequence number for resuming
                        if let Some(s) = data["s"].as_u64() {
                            let mut seq_guard = shared.sequence.lock().await;
                            *seq_guard = Some(s);
                        }

                        // Store session ID for resuming
                        if let Some(t) = data["t"].as_str() {
                            if t == "READY" {
                                if let Some(sid) = data["d"]["session_id"].as_str() {
                                    let mut session_guard = shared.session_id.lock().await;
                                    *session_guard = Some(sid.to_string());
                                }
                            }

                            // Call event handler
                            Python::with_gil(|py| {
                                if let Ok(callbacks) = shared.event_callbacks.lock() {
                                    if let Some(callback) = callbacks.get(t) {
                                        let event_data = data["d"].clone();
                                        let py_data = match pyo3::Python::eval(
                                            py,
                                            &format!("{event_data}"),
                                            None,
                                            None,
                                        )
                                        .and_then(|obj| obj.extract::<PyObject>())
                                        {
                                            Ok(d) => d,
                                            Err(e) => {
                                                eprintln!(
                                                    "Failed to convert event data to Python: {e}"
                                                );
                                                return;
                                            }
                                        };

                                        if let Err(e) = callback.call1(py, (py_data,)) {
                                            eprintln!("Error in event callback: {e}");
                                        }
                                    }
                                }
                            });
                        }
                    }
                    GATEWAY_OP_RECONNECT => {
                        // Server requested reconnect
                        eprintln!("Gateway requested reconnect");
                        break;
                    }
                    GATEWAY_OP_INVALID_SESSION => {
                        // Invalid session, clear session data
                        {
                            let mut sid_guard = shared.session_id.lock().await;
                            *sid_guard = None;
                        }
                        {
                            let mut seq_guard = shared.sequence.lock().await;
                            *seq_guard = None;
                        }
                        eprintln!("Invalid session");

                        // Wait a random amount of time before reconnecting
                        let delay = rand::thread_rng().gen_range(1..5);
                        tokio::time::sleep(Duration::from_secs(delay)).await;
                        break;
                    }
                    GATEWAY_OP_HEARTBEAT_ACK => {
                        // Update last heartbeat acknowledgement time
                        let mut ack_guard = shared.last_heartbeat_ack.lock().await;
                        *ack_guard = Instant::now();
                    }
                    _ => {
                        // Unhandled operation code
                        eprintln!("Unhandled gateway op: {op}");
                    }
                }
            }
            Ok(WsMessage::Close(frame)) => {
                eprintln!("WebSocket closed: {frame:?}");
                break;
            }
            Err(e) => {
                eprintln!("WebSocket error: {e}");
                break;
            }
            _ => {}
        }
    }
}

async fn handle_heartbeats(
    mut heartbeat_rx: mpsc::Receiver<bool>,
    ws_sender: Arc<
        Mutex<
            futures::stream::SplitSink<
                tokio_tungstenite::WebSocketStream<
                    tokio_tungstenite::MaybeTlsStream<tokio::net::TcpStream>,
                >,
                WsMessage,
            >,
        >,
    >,
    shared: Arc<SharedGatewayClient>,
) {
    if heartbeat_rx.recv().await.is_some() {
        let mut interval_timer = interval(Duration::from_secs(1));

        loop {
            interval_timer.tick().await;

            // Get current heartbeat interval
            let Some(heartbeat_ms) = *shared.heartbeat_interval.lock().await else {
                continue;
            };

            // Check if we've received a heartbeat ACK recently
            let last_ack = *shared.last_heartbeat_ack.lock().await;
            if last_ack.elapsed() > Duration::from_millis(heartbeat_ms * 2) {
                eprintln!("Heartbeat ACK not received in time, closing connection");
                break;
            }

            // Time to send a heartbeat?
            let send_heartbeat = {
                static mut LAST_HEARTBEAT: Option<Instant> = None;
                unsafe {
                    let now = Instant::now();
                    let should_send = match LAST_HEARTBEAT {
                        Some(last) => now.duration_since(last).as_millis() >= heartbeat_ms as u128,
                        None => true,
                    };

                    if should_send {
                        LAST_HEARTBEAT = Some(now);
                    }

                    should_send
                }
            };

            if send_heartbeat {
                // Send heartbeat with current sequence number
                let seq = *shared.sequence.lock().await;
                let heartbeat = json!({
                    "op": GATEWAY_OP_HEARTBEAT,
                    "d": seq
                });

                let heartbeat_msg = WsMessage::Text(heartbeat.to_string());

                // Using scoped block to ensure MutexGuard is dropped before await
                {
                    let mut ws_sender_guard = ws_sender.lock().await;
                    if let Err(e) = ws_sender_guard.send(heartbeat_msg).await {
                        eprintln!("Failed to send heartbeat: {e}");
                        break;
                    }
                }
            }
        }
    }
}
