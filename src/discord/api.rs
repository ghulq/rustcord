use super::{
    errors::DiscordError,
    gateway::GatewayData,
    models::{Channel, Guild, Message, User},
    url,
};
use pyo3::{PyClass, prelude::*};
use reqwest::{Client as ReqwestClient, Method, header};
use serde::{Serialize, de::DeserializeOwned};
use serde_json::json;
use std::{sync::Arc, time::Duration};
use tokio::runtime::Runtime;

/// High-performance Rust client for Discord API interactions
#[pyclass]
pub struct DiscordClient {
    http_client: ReqwestClient,
    runtime: Arc<Runtime>,
}

impl DiscordClient {
    fn request<T>(&self, method: Method, url: String, data: Vec<u8>) -> PyResult<T>
    where
        T: DeserializeOwned,
    {
        let client = self.http_client.clone();

        self.runtime
            .block_on(async move {
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

                if !response.status().is_success() {
                    let status = response.status();
                    let error_text = response.text().await;
                    return Err(DiscordError::ApiError(format!(
                        "[{method} {url}] Discord API error: {status} - {}",
                        error_text.as_deref().unwrap_or("Unknown error")
                    )));
                }

                response.json::<T>().await.map_err(|e| {
                    DiscordError::ParseError(format!(
                        "[{method} {url}] Failed to parse response: {e}"
                    ))
                })
            })
            .map_err(|e: DiscordError| e.to_pyerr())
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
    /// Creates a new DiscordClient with the given token
    #[new]
    pub fn new(token: String) -> PyResult<Self> {
        // Create a custom HTTP client with appropriate headers and timeouts
        let mut headers = header::HeaderMap::new();
        let auth_value = format!("Bot {token}");
        headers.insert(
            header::AUTHORIZATION,
            header::HeaderValue::from_str(&auth_value).map_err(
                |e: header::InvalidHeaderValue| {
                    DiscordError::InvalidToken(e.to_string()).to_pyerr()
                },
            )?,
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
            .build()
            .map_err(|e| DiscordError::HttpClientError(e.to_string()).to_pyerr())?;

        // Create a Tokio runtime for async operations
        let runtime =
            Runtime::new().map_err(|e| DiscordError::RuntimeError(e.to_string()).to_pyerr())?;

        Ok(Self {
            http_client,
            runtime: Arc::new(runtime),
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
