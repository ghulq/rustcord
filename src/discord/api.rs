use super::{
    errors::DiscordError,
    gateway::GatewayData,
    models::{Channel, Guild, Message, User},
    url,
};
use dashmap::DashMap;
use pyo3::{prelude::*, PyClass};
use reqwest::{Client as ReqwestClient, Method, header};
use serde::{Serialize, de::DeserializeOwned};
use serde_json::json;
use std::{sync::Arc, time::Duration};
use tokio::runtime::Runtime;

#[pyclass]
pub struct DiscordClient {
    http_client: Arc<ReqwestClient>,
    runtime: Arc<Runtime>,
    cache: Arc<DashMap<String, Vec<u8>>>,
}

impl DiscordClient {
    async fn request_internal<T>(
        client: Arc<ReqwestClient>, 
        method: Method,
        url: String,
        data: Vec<u8>,
        cache: Arc<DashMap<String, Vec<u8>>>,
    ) -> Result<T, DiscordError> 
    where
        T: DeserializeOwned,
    {
        // Check cache for GET requests
        if method == Method::GET {
            if let Some(cached) = cache.get(&url) {
                if let Ok(parsed) = serde_json::from_slice(cached.value()) {
                    return Ok(parsed);
                }
            }
        }

        let response = client
            .request(method.clone(), url.clone())
            .body(data)
            .send()
            .await
            .map_err(|e| {
                DiscordError::ApiError(format!(
                    "[{method} {url}] Failed to send request: {e}"
                ))
            })?;

        let status = response.status();
        if !status.is_success() {
            let error_text = response.text().await;
            return Err(DiscordError::ApiError(format!(
                "[{method} {url}] Discord API error: {status} - {}",
                error_text.unwrap_or_else(|_| "Unknown error".to_string())
            )));
        }

        let bytes = response.bytes().await.map_err(|e| {
            DiscordError::ParseError(format!(
                "[{method} {url}] Failed to get response bytes: {e}"
            ))
        })?;

        // Cache successful GET responses
        if method == Method::GET {
            cache.insert(url.clone(), bytes.to_vec());
        }

        serde_json::from_slice(&bytes).map_err(|e| {
            DiscordError::ParseError(format!(
                "[{method} {url}] Failed to parse response: {e}"
            ))
        })
    }

    fn request<T>(&self, method: Method, url: String, data: Vec<u8>) -> PyResult<T>
    where
        T: DeserializeOwned,
    {
        let client = self.http_client.clone();
        let cache = self.cache.clone();

        self.runtime
            .block_on(Self::request_internal(client, method, url, data, cache))
            .map_err(|e| e.to_pyerr())
    }

    fn get<T>(&self, url: String, py: Python) -> PyResult<Py<T>>
    where
        T: DeserializeOwned + PyClass + Into<PyClassInitializer<T>>,
    {
        self.request(Method::GET, url, Default::default())
            .and_then(|data: T| Py::new(py, data))
    }

    fn get_vec<T>(&self, url: String, py: Python) -> PyResult<Vec<Py<T>>>
    where
        T: DeserializeOwned + PyClass + Into<PyClassInitializer<T>>,
    {
        self.request(Method::GET, url, Default::default())
            .and_then(|data: Vec<T>| {
                let mut output = Vec::with_capacity(data.len());

                for element in data {
                    output.push(Py::new(py, element)?);
                }

                Ok(output)
            })
    }

    fn post<T, D>(&self, url: String, data: &D, py: Python) -> PyResult<Py<T>>
    where
        T: DeserializeOwned + PyClass + Into<PyClassInitializer<T>>,
        D: Serialize + ?Sized,
    {
        self.request(Method::POST, url, serde_json::to_vec(data).unwrap())
            .and_then(|data: T| Py::new(py, data))
    }
}

#[pymethods]
impl DiscordClient {
    #[new]
    pub fn new(token: String) -> PyResult<Self> {
        let mut headers = header::HeaderMap::with_capacity(3);
        headers.insert(
            header::AUTHORIZATION,
            header::HeaderValue::from_str(&format!("Bot {token}"))
                .map_err(|e| DiscordError::InvalidToken(e.to_string()).to_pyerr())?,
        );

        headers.insert(
            header::CONTENT_TYPE,
            header::HeaderValue::from_static("application/json"),
        );

        headers.insert(
            header::USER_AGENT,
            header::HeaderValue::from_static("RustCord (https://github.com/user/rustcord, 0.1.3)"),
        );

        let http_client = ReqwestClient::builder()
            .default_headers(headers)
            .timeout(Duration::from_secs(30))
            .pool_idle_timeout(Duration::from_secs(90))
            .tcp_keepalive(Duration::from_secs(60))
            .build()
            .map_err(|e| DiscordError::HttpClientError(e.to_string()).to_pyerr())?;

        let runtime = Runtime::new()
            .map_err(|e| DiscordError::RuntimeError(e.to_string()).to_pyerr())?;

        Ok(Self {
            http_client: Arc::new(http_client),
            runtime: Arc::new(runtime),
            cache: Arc::new(DashMap::new()),
        })
    }

    /// Send a message to a channel
    pub fn send_message(
        &self,
        channel_id: String,
        content: String,
        py: Python,
    ) -> PyResult<Py<Message>> {
        self.post(
            url!("/channels/{}/messages", channel_id),
            &json!({ "content": content }),
            py,
        )
    }

    /// Get a channel by ID
    pub fn get_channel(&self, channel_id: String, py: Python) -> PyResult<Py<Channel>> {
        self.get(url!("/channels/{}", channel_id), py)
    }

    /// Get the current bot user
    pub fn get_current_user(&self, py: Python) -> PyResult<Py<User>> {
        self.get(url!("/users/@me"), py)
    }

    /// Get guilds for the current user
    pub fn get_current_user_guilds(&self, py: Python) -> PyResult<Vec<Py<Guild>>> {
        self.get_vec(url!("/users/@me/guilds"), py)
    }

    /// Get the gateway URL for websocket connections
    pub fn get_gateway_url(&self) -> PyResult<String> {
        self.request(Method::GET, url!("/gateway"), Default::default())
            .and_then(|gateway_data: GatewayData| {
                gateway_data.url.ok_or_else(|| {
                    DiscordError::ParseError("Gateway URL not found in response".to_string())
                        .to_pyerr()
                })
            })
    }
}
