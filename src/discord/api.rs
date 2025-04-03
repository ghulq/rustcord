use crate::discord::errors::DiscordError;
use crate::discord::models::{Message, Channel, User, Guild};
use crate::discord::{API_BASE_URL, API_VERSION};
use pyo3::prelude::*;
use reqwest::{Client as ReqwestClient, header};
use serde_json::json;
use std::sync::Arc;
use std::time::Duration;
use tokio::runtime::Runtime;

/// High-performance Rust client for Discord API interactions
#[pyclass]
pub struct DiscordClient {
    token: String,
    http_client: ReqwestClient,
    runtime: Arc<Runtime>,
}

#[pymethods]
impl DiscordClient {
    /// Creates a new DiscordClient with the given token
    #[new]
    pub fn new(token: String) -> PyResult<Self> {
        // Create a custom HTTP client with appropriate headers and timeouts
        let mut headers = header::HeaderMap::new();
        let auth_value = format!("Bot {}", token);
        headers.insert(
            header::AUTHORIZATION,
            header::HeaderValue::from_str(&auth_value).map_err(|e| {
                DiscordError::InvalidToken(e.to_string()).to_pyerr()
            })?,
        );
        
        headers.insert(
            header::CONTENT_TYPE,
            header::HeaderValue::from_static("application/json"),
        );
        
        headers.insert(
            header::USER_AGENT,
            header::HeaderValue::from_static("RustCord (https://github.com/user/rustcord, 0.1.0)"),
        );
        
        let http_client = ReqwestClient::builder()
            .default_headers(headers)
            .timeout(Duration::from_secs(30))
            .build()
            .map_err(|e| DiscordError::HttpClientError(e.to_string()).to_pyerr())?;
        
        // Create a Tokio runtime for async operations
        let runtime = Runtime::new()
            .map_err(|e| DiscordError::RuntimeError(e.to_string()).to_pyerr())?;
        
        Ok(Self {
            token,
            http_client,
            runtime: Arc::new(runtime),
        })
    }
    
    /// Send a message to a channel
    pub fn send_message(&self, channel_id: String, content: String, py: Python) -> PyResult<Py<Message>> {
        let client = self.http_client.clone();
        let url = format!("{}/v{}/channels/{}/messages", API_BASE_URL, API_VERSION, channel_id);
        let data = json!({ "content": content });
        
        self.runtime.block_on(async move {
            let response = client.post(&url)
                .json(&data)
                .send()
                .await
                .map_err(|e| DiscordError::ApiError(format!("Failed to send message: {}", e)))?;
            
            if !response.status().is_success() {
                let status = response.status();
                let error_text = response.text().await.unwrap_or_else(|_| "Unknown error".to_string());
                return Err(DiscordError::ApiError(format!(
                    "Discord API error: {} - {}", 
                    status, 
                    error_text
                )));
            }
            
            let message_data = response.json().await
                .map_err(|e| DiscordError::ParseError(format!("Failed to parse message response: {}", e)))?;
            
            Ok(Message::from_json(message_data))
        })
        .map_err(|e: DiscordError| e.to_pyerr())
        .and_then(|msg| Py::new(py, msg))
    }
    
    /// Get a channel by ID
    pub fn get_channel(&self, channel_id: String, py: Python) -> PyResult<Py<Channel>> {
        let client = self.http_client.clone();
        let url = format!("{}/v{}/channels/{}", API_BASE_URL, API_VERSION, channel_id);
        
        self.runtime.block_on(async move {
            let response = client.get(&url)
                .send()
                .await
                .map_err(|e| DiscordError::ApiError(format!("Failed to get channel: {}", e)))?;
            
            if !response.status().is_success() {
                let status = response.status();
                let error_text = response.text().await.unwrap_or_else(|_| "Unknown error".to_string());
                return Err(DiscordError::ApiError(format!(
                    "Discord API error: {} - {}", 
                    status, 
                    error_text
                )));
            }
            
            let channel_data = response.json().await
                .map_err(|e| DiscordError::ParseError(format!("Failed to parse channel response: {}", e)))?;
            
            Ok(Channel::from_json(channel_data))
        })
        .map_err(|e: DiscordError| e.to_pyerr())
        .and_then(|channel| Py::new(py, channel))
    }
    
    /// Get the current bot user
    pub fn get_current_user(&self, py: Python) -> PyResult<Py<User>> {
        let client = self.http_client.clone();
        let url = format!("{}/v{}/users/@me", API_BASE_URL, API_VERSION);
        
        self.runtime.block_on(async move {
            let response = client.get(&url)
                .send()
                .await
                .map_err(|e| DiscordError::ApiError(format!("Failed to get current user: {}", e)))?;
            
            if !response.status().is_success() {
                let status = response.status();
                let error_text = response.text().await.unwrap_or_else(|_| "Unknown error".to_string());
                return Err(DiscordError::ApiError(format!(
                    "Discord API error: {} - {}", 
                    status, 
                    error_text
                )));
            }
            
            let user_data = response.json().await
                .map_err(|e| DiscordError::ParseError(format!("Failed to parse user response: {}", e)))?;
            
            Ok(User::from_json(user_data))
        })
        .map_err(|e: DiscordError| e.to_pyerr())
        .and_then(|user| Py::new(py, user))
    }
    
    /// Get guilds for the current user
    pub fn get_current_user_guilds(&self, py: Python) -> PyResult<Vec<Py<Guild>>> {
        let client = self.http_client.clone();
        let url = format!("{}/v{}/users/@me/guilds", API_BASE_URL, API_VERSION);
        
        self.runtime.block_on(async move {
            let response = client.get(&url)
                .send()
                .await
                .map_err(|e| DiscordError::ApiError(format!("Failed to get guilds: {}", e)))?;
            
            if !response.status().is_success() {
                let status = response.status();
                let error_text = response.text().await.unwrap_or_else(|_| "Unknown error".to_string());
                return Err(DiscordError::ApiError(format!(
                    "Discord API error: {} - {}", 
                    status, 
                    error_text
                )));
            }
            
            let guilds_data: Vec<serde_json::Value> = response.json().await
                .map_err(|e| DiscordError::ParseError(format!("Failed to parse guilds response: {}", e)))?;
            
            let mut result = Vec::with_capacity(guilds_data.len());
            for guild_data in guilds_data {
                result.push(Guild::from_json(guild_data));
            }
            
            Ok(result)
        })
        .map_err(|e: DiscordError| e.to_pyerr())
        .and_then(|guilds| {
            let mut py_guilds = Vec::with_capacity(guilds.len());
            for guild in guilds {
                py_guilds.push(Py::new(py, guild)?);
            }
            Ok(py_guilds)
        })
    }
    
    /// Get the gateway URL for websocket connections
    pub fn get_gateway_url(&self) -> PyResult<String> {
        let client = self.http_client.clone();
        let url = format!("{}/v{}/gateway", API_BASE_URL, API_VERSION);
        
        self.runtime.block_on(async move {
            let response = client.get(&url)
                .send()
                .await
                .map_err(|e| DiscordError::ApiError(format!("Failed to get gateway URL: {}", e)))?;
            
            if !response.status().is_success() {
                let status = response.status();
                let error_text = response.text().await.unwrap_or_else(|_| "Unknown error".to_string());
                return Err(DiscordError::ApiError(format!(
                    "Discord API error: {} - {}", 
                    status, 
                    error_text
                )));
            }
            
            let gateway_data: serde_json::Value = response.json().await
                .map_err(|e| DiscordError::ParseError(format!("Failed to parse gateway response: {}", e)))?;
            
            gateway_data.get("url")
                .and_then(|url| url.as_str())
                .map(|url| url.to_string())
                .ok_or_else(|| DiscordError::ParseError("Gateway URL not found in response".to_string()))
        })
        .map_err(|e: DiscordError| e.to_pyerr())
    }
}
