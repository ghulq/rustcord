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
use std::{collections::HashMap, sync::Arc, time::{Duration, Instant}};
use tokio::runtime::Runtime;
use tracing::{debug, warn};

#[pyclass]
pub struct DiscordClient {
    http_client: Arc<ReqwestClient>,
    runtime: Arc<Runtime>,
    cache: Arc<DashMap<String, Vec<u8>>>,
    rate_limits: Arc<DashMap<String, Arc<RateLimitBucket>>>,
}

#[derive(Debug)]
struct RateLimitBucket {
    remaining: tokio::sync::Mutex<Option<u64>>,
    reset_at: tokio::sync::Mutex<Option<Instant>>,
    total_requests: tokio::sync::Mutex<u64>,
    total_retries: tokio::sync::Mutex<u64>,
    last_used: tokio::sync::Mutex<Option<Instant>>,
}

impl RateLimitBucket {
    fn new() -> Self {
        Self {
            remaining: tokio::sync::Mutex::new(None),
            reset_at: tokio::sync::Mutex::new(None),
            total_requests: tokio::sync::Mutex::new(0),
            total_retries: tokio::sync::Mutex::new(0),
            last_used: tokio::sync::Mutex::new(None),
        }
    }

    async fn increment_requests(&self) {
        let mut reqs = self.total_requests.lock().await;
        *reqs += 1;
        let mut last = self.last_used.lock().await;
        *last = Some(Instant::now());
    }

    async fn increment_retries(&self) {
        let mut retries = self.total_retries.lock().await;
        *retries += 1;
    }

    async fn get_metrics(&self) -> HashMap<String, u64> {
        let mut metrics = HashMap::new();
        metrics.insert("total_requests".to_string(), *self.total_requests.lock().await);
        metrics.insert("total_retries".to_string(), *self.total_retries.lock().await);
        if let Some(remaining) = *self.remaining.lock().await {
            metrics.insert("remaining".to_string(), remaining);
        }
        metrics
    }
}

/// Normalize a Discord API route following official rules to reduce bucket count
/// This follows Discord's route normalization rules:
/// 1. Major parameters that are snowflakes are kept as is
/// 2. Minor parameters are replaced with their names (reactions, messages in bulk delete, etc)
/// 3. Trailing slash is preserved
/// See: https://discord.com/developers/docs/topics/rate-limits
fn normalize_route(method: &Method, path: &str) -> String {
    let parts: Vec<&str> = path.split('/').collect();
    let mut normalized = Vec::with_capacity(parts.len());
    
    for (i, part) in parts.iter().enumerate() {
        if part.is_empty() { 
            continue;
        }

        // Handle special cases for major parameters (preserved snowflakes)
        match *part {
            // Channels
            p if i >= 2 && parts.get(i-2) == Some(&"channels") => {
                match p {
                    "messages" | "pins" | "invites" | "webhooks" | "typing" 
                    | "permissions" | "followers" | "recipients" | "reactions" => normalized.push(*part),
                    _ => normalized.push(":channel_id") // Normalize channel operations
                }
            },
            // Messages
            p if i >= 2 && parts.get(i-2) == Some(&"messages") => {
                match p {
                    "bulk-delete" | "crosspost" => normalized.push(*part),
                    _ => normalized.push(":message_id")
                }
            },
            // Guilds
            p if i >= 2 && parts.get(i-2) == Some(&"guilds") => {
                match p {
                    "members" | "bans" | "roles" | "prune" | "regions" | "invites" 
                    | "integrations" | "emojis" | "audit-logs" => normalized.push(*part),
                    _ => normalized.push(":guild_id")
                }
            },
            // webhooks
            p if i >= 2 && parts.get(i-2) == Some(&"webhooks") => {
                match p {
                    "slack" | "github" => normalized.push(*part),
                    _ => normalized.push(":webhook_id")
                }
            },
            // Keep other parts as is
            _ => normalized.push(*part)
        };
    }

    // Preserve trailing slash if present
    let trailing_slash = path.ends_with('/');
    let mut route = normalized.join("/");
    if trailing_slash {
        route.push('/');
    }

    format!("{} /{}", method.as_str(), route)
}

impl DiscordClient {
    async fn request_internal<T>(
        client: Arc<ReqwestClient>, 
        method: Method,
        url: String,
        data: Vec<u8>,
        cache: Arc<DashMap<String, Vec<u8>>>,
        rate_limits: Arc<DashMap<String, Arc<RateLimitBucket>>>,
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

        // Normalize the route for proper bucket handling
        let path_only = match url.find('?') {
            Some(i) => &url[..i],
            None => &url[..],
        };
        let route_key = normalize_route(&method, path_only);
        debug!(?route_key, "Normalized route for request");

        // If we have a bucket and it's exhausted, wait until reset
        if let Some(bucket_entry) = rate_limits.get(&route_key) {
            let bucket = bucket_entry.value().clone();
            if let Some(remaining) = *bucket.remaining.lock().await {
                if remaining == 0 {
                    if let Some(reset_at) = *bucket.reset_at.lock().await {
                        let now = Instant::now();
                        if reset_at > now {
                            let wait = reset_at.duration_since(now);
                            tokio::time::sleep(wait).await;
                        }
                    }
                }
            }
        }

        // Basic retry loop to handle 429 rate-limits with Retry-After
        let mut attempts = 0u8;
        let bytes = loop {
            let resp_result = client
                .request(method.clone(), url.clone())
                .body(data.clone())
                .send()
                .await
                .map_err(|e| {
                    DiscordError::ApiError(format!(
                        "[{method} {url}] Failed to send request: {e}"
                    ))
                })?;

            // Clone headers early so we can update rate-limit state later
            let headers = resp_result.headers().clone();
            let status = resp_result.status();

            if status.as_u16() == 429 {
                // Rate limited; attempt to read Retry-After header or body
                attempts = attempts.saturating_add(1);
                
                // Update bucket metrics
                if let Some(bucket_arc) = rate_limits.get(&route_key) {
                    bucket_arc.increment_retries().await;
                }
                warn!(?route_key, attempts, "Rate limit hit");

                let mut retry_after = None::<f64>;

                if let Some(h) = headers.get("retry-after") {
                    if let Ok(s) = h.to_str() {
                        if let Ok(f) = s.parse::<f64>() {
                            retry_after = Some(f);
                        }
                    }
                }

                // Try to find retry_after in body if header missing
                if retry_after.is_none() {
                    if let Ok(text) = resp_result.text().await {
                        if let Ok(json_val) = serde_json::from_str::<serde_json::Value>(&text) {
                            if let Some(v) = json_val.get("retry_after") {
                                if v.is_number() {
                                    retry_after = v.as_f64();
                                }
                            }
                        }
                    }
                }

                // Default backoff if not provided
                let wait_secs = retry_after.unwrap_or(1.0_f64);
                let wait_duration = std::time::Duration::from_secs_f64(wait_secs);

                // If bucket id is provided, update/reset the bucket information
                if let Some(bucket_id_h) = headers.get("x-ratelimit-bucket") {
                    if let Ok(bucket_id) = bucket_id_h.to_str() {
                        let bucket_key = bucket_id.to_string();
                        let bucket_arc = rate_limits.get(&bucket_key).map(|v| v.value().clone()).unwrap_or_else(|| {
                            let b = Arc::new(RateLimitBucket::new());
                            rate_limits.insert(bucket_key.clone(), b.clone());
                            b
                        });

                        // set reset_at based on retry_after
                        if let Some(secs) = retry_after {
                            let mut reset_guard = bucket_arc.reset_at.lock().await;
                            *reset_guard = Some(Instant::now() + Duration::from_secs_f64(secs));
                        }
                        // mark remaining as zero until reset
                        let mut rem_guard = bucket_arc.remaining.lock().await;
                        *rem_guard = Some(0);
                    }
                }

                if attempts >= 5 {
                    return Err(DiscordError::ApiError(format!(
                        "[{method} {url}] Rate limited and retry attempts exhausted"
                    )));
                }

                tokio::time::sleep(wait_duration).await;
                continue; // retry
            }

            if !status.is_success() {
                let error_text = resp_result.text().await;
                return Err(DiscordError::ApiError(format!(
                    "[{method} {url}] Discord API error: {status} - {}",
                    error_text.unwrap_or_else(|_| "Unknown error".to_string())
                )));
            }

            // Update rate limit info from headers for successful responses
            // Determine bucket key (prefer x-ratelimit-bucket header)
            let bucket_key = headers
                .get("x-ratelimit-bucket")
                .and_then(|v| v.to_str().ok())
                .map(|s| s.to_string())
                .unwrap_or_else(|| route_key.clone());

            let bucket_arc = rate_limits.get(&bucket_key).map(|v| v.value().clone()).unwrap_or_else(|| {
                let b = Arc::new(RateLimitBucket::new());
                rate_limits.insert(bucket_key.clone(), b.clone());
                debug!(?bucket_key, "Created new rate limit bucket");
                b
            });
            
            // Update bucket metrics for the request
            bucket_arc.increment_requests().await;

            if let Some(h) = headers.get("x-ratelimit-remaining") {
                if let Ok(s) = h.to_str() {
                    if let Ok(n) = s.parse::<u64>() {
                        let mut rem_guard = bucket_arc.remaining.lock().await;
                        *rem_guard = Some(n);
                    }
                }
            }

            if let Some(h) = headers.get("x-ratelimit-reset-after") {
                if let Ok(s) = h.to_str() {
                    if let Ok(f) = s.parse::<f64>() {
                        let mut reset_guard = bucket_arc.reset_at.lock().await;
                        *reset_guard = Some(Instant::now() + Duration::from_secs_f64(f));
                    }
                }
            }

            // bytes is consumed from the response -- we can now return it
            break resp_result.bytes().await.map_err(|e| {
                DiscordError::ParseError(format!(
                    "[{method} {url}] Failed to get response bytes: {e}"
                ))
            })?;
        };

        // After successful response, update rate limit info from headers (if present)
        // Re-send the request bytes above provided the response succeeded and we've broken out
        // Note: we need to re-request headers by making a lightweight HEAD-like request isn't possible here,
        // but since `resp_result` was consumed we can re-run a second request to fetch headers only if desired.
        // Instead, we will perform a fresh lightweight request to HEAD the same URL to get headers when needed.
        // For simplicity and to avoid extra network calls, we will skip header-based updates here.

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
            .block_on(Self::request_internal(client, method, url, data, cache, self.rate_limits.clone()))
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
    /// Get metrics for all rate limit buckets
    pub fn get_rate_limit_metrics(&self, py: Python) -> PyResult<PyObject> {
        let metrics = self.runtime.block_on(async {
            let mut all_metrics = HashMap::new();
            for entry in self.rate_limits.iter() {
                let bucket_metrics = entry.value().get_metrics().await;
                all_metrics.insert(entry.key().clone(), bucket_metrics);
            }
            all_metrics
        });
        
        // Convert to Python dict
        Ok(metrics.into_py(py))
    }

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
            rate_limits: Arc::new(DashMap::new()),
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
        // Prefer using /gateway/bot for bots to receive recommended shard info
        let bot_gateway = self.request::<GatewayData>(Method::GET, url!("/gateway/bot"), Default::default());

        if let Ok(gateway_data) = bot_gateway {
            return gateway_data
                .url
                .ok_or_else(||
                    DiscordError::ParseError("Gateway URL not found in /gateway/bot response".to_string())
                        .to_pyerr()
                );
        }

        // Fallback to /gateway if /gateway/bot is not available or fails
        self.request::<GatewayData>(Method::GET, url!("/gateway"), Default::default())
            .and_then(|gateway_data: GatewayData| {
                gateway_data.url.ok_or_else(|| {
                    DiscordError::ParseError("Gateway URL not found in response".to_string())
                        .to_pyerr()
                })
            })
    }
}
