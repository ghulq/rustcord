use super::{errors::DiscordError, util};
use dashmap::DashMap;
use futures::{SinkExt, StreamExt};
use pyo3::{prelude::*, types::PyDict};
use rand::Rng;
use serde::Deserialize;
use serde_json::{Value, json};
use std::{
    sync::Arc,
    time::{Duration, SystemTime},
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

#[allow(dead_code)]
struct SharedGatewayClient {
    token: String,
    runtime: Runtime,
    last_heartbeat_ack: tokio::sync::Mutex<SystemTime>,
    session_id: tokio::sync::Mutex<Option<String>>,
    sequence: tokio::sync::Mutex<Option<u64>>,
    event_callbacks: DashMap<String, PyObject>,
    heartbeat_interval: tokio::sync::Mutex<Option<u64>>,
    connection_attempts: tokio::sync::Mutex<u32>,
}

impl SharedGatewayClient {
    fn new(token: String, runtime: Runtime) -> Self {
        Self {
            token,
            runtime,
            last_heartbeat_ack: tokio::sync::Mutex::new(SystemTime::now()),
            session_id: tokio::sync::Mutex::default(),
            sequence: tokio::sync::Mutex::default(),
            event_callbacks: DashMap::new(),
            heartbeat_interval: tokio::sync::Mutex::default(),
            connection_attempts: tokio::sync::Mutex::new(0),
        }
    }

    #[allow(dead_code)]
    async fn increment_connection_attempts(&self) -> u32 {
        let mut attempts = self.connection_attempts.lock().await;
        *attempts += 1;
        *attempts
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
        let runtime =
            Runtime::new().map_err(|e| DiscordError::RuntimeError(e.to_string()).to_pyerr())?;

        Ok(Self {
            shared: Arc::new(SharedGatewayClient::new(token, runtime)),
            message_tx: None,
            intents,
        })
    }

    /// Register a callback for a specific gateway event (sync-friendly)
    pub fn on(&self, event_name: String, callback: PyObject) -> PyResult<()> {
        self.shared.event_callbacks.insert(event_name, callback);
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
    if !gateway_url.contains('?') {
        gateway_url.push_str("?v=10&encoding=json");
    }

    let gateway_url = Url::parse(&gateway_url)
        .map_err(|e| DiscordError::ParseError(format!("Invalid gateway URL: {e}")))?;

    let (ws_stream, _) = connect_async(gateway_url)
        .await
        .map_err(|e| DiscordError::ConnectionError(format!("WebSocket connection failed: {e}")))?;

    println!("Connected to Discord Gateway");

    let (ws_sender, mut ws_receiver) = ws_stream.split();
    let ws_sender = Arc::new(Mutex::new(ws_sender));

    let (heartbeat_tx, heartbeat_rx) = mpsc::channel::<bool>(1);

    let ws_sender_clone1 = ws_sender.clone();
    let shared_cloned = shared.clone();

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

    let ws_sender_clone2 = ws_sender.clone();
    let shared_cloned2 = shared.clone();

    tokio::spawn(async move {
        handle_heartbeats(heartbeat_rx, ws_sender_clone2, shared_cloned2).await;
    });

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
                let data: Value = match serde_json::from_str(&text) {
                    Ok(data) => data,
                    Err(e) => {
                        eprintln!("Failed to parse gateway message: {e}");
                        continue;
                    }
                };

                let op = data["op"].as_u64().unwrap_or(99);

                match op as u8 {
                    GATEWAY_OP_HELLO => {
                        if let Some(interval_ms) = data["d"]["heartbeat_interval"].as_u64() {
                            let mut interval_guard = shared.heartbeat_interval.lock().await;
                            *interval_guard = Some(interval_ms);
                            heartbeat_tx.send(true).await.ok();

                            // IDENTIFY or RESUME
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

                                if let (Some(shard_id), Some(shard_count)) = (shard_id, shard_count) {
                                    println!("Sending IDENTIFY with shard [{shard_id}]/[{shard_count}]");
                                    json["d"]["shard"] = json!([shard_id, shard_count]);
                                }

                                json
                            };

                            let identify_msg = WsMessage::Text(identify.to_string());
                            {
                                let mut ws_sender_guard = ws_sender.lock().await;
                                if let Err(e) = ws_sender_guard.send(identify_msg).await {
                                    eprintln!("Failed to send IDENTIFY: {e}");
                                }
                            }
                        }
                    }
                    GATEWAY_OP_DISPATCH => {
                        if let Some(s) = data["s"].as_u64() {
                            let mut seq_guard = shared.sequence.lock().await;
                            *seq_guard = Some(s);
                        }

                        if let Some(t) = data["t"].as_str() {
                            if t == "READY" {
                                if let Some(sid) = data["d"]["session_id"].as_str() {
                                    let mut session_guard = shared.session_id.lock().await;
                                    *session_guard = Some(sid.to_string());
                                }
                            }

                            let callback_opt: Option<PyObject> = shared
                                .event_callbacks
                                .get(t)
                                .map(|entry| entry.clone()); // clone PyObject (GIL-independent)

                            if let Some(callback) = callback_opt {
                                // Convert JSON payload to a Python object via json.loads
                                Python::with_gil(|py| {
                                    let py_json = py.import("json").and_then(|m| {
                                        let s = serde_json::to_string(&data["d"]).unwrap_or_else(|_| "null".to_string());
                                        m.getattr("loads")?.call1((s,))
                                    });

                                    match py_json {
                                        Ok(py_obj) => {
                                            if let Err(e) = callback.call1(py, (py_obj,)) {
                                                eprintln!("Error in event callback: {e}");
                                            }
                                        }
                                        Err(e) => {
                                            eprintln!("Failed to convert event data to Python: {e}");
                                        }
                                    }
                                });
                            }
                        }
                    }
                    GATEWAY_OP_RECONNECT => {
                        eprintln!("Gateway requested reconnect");
                        break;
                    }
                    GATEWAY_OP_INVALID_SESSION => {
                        {
                            let mut sid_guard = shared.session_id.lock().await;
                            *sid_guard = None;
                        }
                        {
                            let mut seq_guard = shared.sequence.lock().await;
                            *seq_guard = None;
                        }
                        eprintln!("Invalid session");
                        let delay = rand::thread_rng().gen_range(1..5);
                        tokio::time::sleep(Duration::from_secs(delay)).await;
                        break;
                    }
                    GATEWAY_OP_HEARTBEAT_ACK => {
                        let mut ack_guard = shared.last_heartbeat_ack.lock().await;
                        *ack_guard = SystemTime::now();
                    }
                    _ => {
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

            let Some(heartbeat_ms) = *shared.heartbeat_interval.lock().await else {
                continue;
            };

            let last_ack = *shared.last_heartbeat_ack.lock().await;
            if let Ok(elapsed) = last_ack.elapsed() {
                if elapsed > Duration::from_millis(heartbeat_ms * 2) {
                    eprintln!("Heartbeat ACK not received in time, closing connection");
                    break;
                }
            } else {
                eprintln!("Failed to calculate elapsed time since last heartbeat ACK");
                break;
            }

            // naive throttle: send if elapsed >= heartbeat_ms
            let send_heartbeat = {
                static mut LAST_HEARTBEAT: Option<SystemTime> = None;
                unsafe {
                    let now = SystemTime::now();
                    let should_send = match LAST_HEARTBEAT {
                        Some(last) => now.duration_since(last).map(|d| d.as_millis() >= heartbeat_ms as u128).unwrap_or(true),
                        None => true,
                    };
                    if should_send {
                        LAST_HEARTBEAT = Some(now);
                    }
                    should_send
                }
            };

            if send_heartbeat {
                let seq = *shared.sequence.lock().await;
                let heartbeat = json!({ "op": GATEWAY_OP_HEARTBEAT, "d": seq });
                let heartbeat_msg = WsMessage::Text(heartbeat.to_string());

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