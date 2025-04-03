use super::util;
use pyo3::prelude::*;
use serde::Deserialize;
use serde_json::Value;

/// Voice State model for Discord voice connections
#[pyclass]
#[derive(Clone, Deserialize)]
pub struct VoiceState {
    #[pyo3(get)]
    #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
    pub guild_id: Option<String>,
    #[pyo3(get)]
    #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
    pub channel_id: Option<String>,
    #[pyo3(get)]
    #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
    pub user_id: String,
    #[pyo3(get)]
    #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
    pub session_id: String,
    #[pyo3(get)]
    #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
    pub deaf: bool,
    #[pyo3(get)]
    #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
    pub mute: bool,
    #[pyo3(get)]
    #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
    pub self_deaf: bool,
    #[pyo3(get)]
    #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
    pub self_mute: bool,
    #[pyo3(get)]
    #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
    pub self_stream: bool,
    #[pyo3(get)]
    #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
    pub self_video: bool,
    #[pyo3(get)]
    #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
    pub suppress: bool,
}

#[pymethods]
impl VoiceState {
    #[new]
    pub const fn new(
        user_id: String,
        session_id: String,
        guild_id: Option<String>,
        channel_id: Option<String>,
        deaf: bool,
        mute: bool,
        self_deaf: bool,
        self_mute: bool,
        self_stream: bool,
        self_video: bool,
        suppress: bool,
    ) -> Self {
        Self {
            guild_id,
            channel_id,
            user_id,
            session_id,
            deaf,
            mute,
            self_deaf,
            self_mute,
            self_stream,
            self_video,
            suppress,
        }
    }

    pub fn __str__(&self) -> String {
        format!(
            "<VoiceState user_id={} channel_id={}>",
            self.user_id,
            self.channel_id.as_deref().unwrap_or("None"),
        )
    }

    pub fn __repr__(&self) -> String {
        format!(
            "VoiceState(user_id='{}', session_id='{}', channel_id={}, guild_id={})",
            self.user_id,
            self.session_id,
            match &self.channel_id {
                Some(id) => format!("'{id}'"),
                None => "None".to_string(),
            },
            match &self.guild_id {
                Some(id) => format!("'{id}'"),
                None => "None".to_string(),
            }
        )
    }
}

impl VoiceState {
    pub fn from_json(data: Value) -> Self {
        serde_json::from_value(data).unwrap()
    }
}

/// Voice Server information from Discord
#[pyclass]
#[derive(Clone, Deserialize)]
pub struct VoiceServerInfo {
    #[pyo3(get)]
    #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
    pub token: String,
    #[pyo3(get)]
    #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
    pub guild_id: String,
    #[pyo3(get)]
    #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
    pub endpoint: String,
}

#[pymethods]
impl VoiceServerInfo {
    #[new]
    pub const fn new(token: String, guild_id: String, endpoint: String) -> Self {
        Self {
            token,
            guild_id,
            endpoint,
        }
    }

    pub fn __str__(&self) -> String {
        format!(
            "<VoiceServerInfo guild_id={} endpoint={}>",
            self.guild_id, self.endpoint
        )
    }

    pub fn __repr__(&self) -> String {
        format!(
            "VoiceServerInfo(token='{}', guild_id='{}', endpoint='{}')",
            self.token, self.guild_id, self.endpoint
        )
    }
}

impl VoiceServerInfo {
    pub fn from_json(data: Value) -> Self {
        serde_json::from_value(data).unwrap()
    }
}

/// Discord Message model
#[pyclass]
#[derive(Clone)]
pub struct Message {
    #[pyo3(get)]
    pub id: String,
    #[pyo3(get)]
    pub channel_id: String,
    #[pyo3(get)]
    pub content: String,
    #[pyo3(get)]
    pub author_id: String,
    #[pyo3(get)]
    pub author_username: String,
}

#[pymethods]
impl Message {
    #[new]
    pub const fn new(
        id: String,
        channel_id: String,
        content: String,
        author_id: String,
        author_username: String,
    ) -> Self {
        Self {
            id,
            channel_id,
            content,
            author_id,
            author_username,
        }
    }

    pub fn __str__(&self) -> String {
        format!("<Message id={} content={}>", self.id, self.content)
    }

    pub fn __repr__(&self) -> String {
        format!(
            "Message(id='{}', channel_id='{}', content='{}', author_id='{}', author_username='{}')",
            self.id, self.channel_id, self.content, self.author_id, self.author_username
        )
    }
}

impl Message {
    pub fn from_json(data: Value) -> Self {
        let id = data
            .get("id")
            .and_then(|v| v.as_str())
            .unwrap_or_default()
            .to_string();

        let channel_id = data
            .get("channel_id")
            .and_then(|v| v.as_str())
            .unwrap_or_default()
            .to_string();

        let content = data
            .get("content")
            .and_then(|v| v.as_str())
            .unwrap_or_default()
            .to_string();

        let author_id = data
            .get("author")
            .and_then(|v| v.get("id"))
            .and_then(|v| v.as_str())
            .unwrap_or_default()
            .to_string();

        let author_username = data
            .get("author")
            .and_then(|v| v.get("username"))
            .and_then(|v| v.as_str())
            .unwrap_or_default()
            .to_string();

        Self {
            id,
            channel_id,
            content,
            author_id,
            author_username,
        }
    }
}

/// Discord User model
#[pyclass]
#[derive(Clone, Deserialize)]
pub struct User {
    #[pyo3(get)]
    #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
    pub id: String,
    #[pyo3(get)]
    #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
    pub username: String,
    #[pyo3(get)]
    #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
    pub discriminator: String,
    #[pyo3(get)]
    #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
    pub bot: bool,
}

#[pymethods]
impl User {
    #[new]
    pub const fn new(id: String, username: String, discriminator: String, bot: bool) -> Self {
        Self {
            id,
            username,
            discriminator,
            bot,
        }
    }

    pub fn __str__(&self) -> String {
        format!("<User id={} username={}>", self.id, self.username)
    }

    pub fn __repr__(&self) -> String {
        format!(
            "User(id='{}', username='{}', discriminator='{}', bot={})",
            self.id, self.username, self.discriminator, self.bot
        )
    }
}

impl User {
    pub fn from_json(data: Value) -> Self {
        serde_json::from_value(data).unwrap()
    }
}

/// Discord Channel model
#[pyclass]
#[derive(Clone, Deserialize)]
pub struct Channel {
    #[pyo3(get)]
    #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
    pub id: String,
    #[pyo3(get)]
    #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
    pub name: String,
    #[pyo3(get)]
    #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
    pub channel_type: u8,
    #[pyo3(get)]
    #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
    pub guild_id: Option<String>,
}

#[pymethods]
impl Channel {
    #[new]
    pub const fn new(id: String, name: String, channel_type: u8, guild_id: Option<String>) -> Self {
        Self {
            id,
            name,
            channel_type,
            guild_id,
        }
    }

    pub fn __str__(&self) -> String {
        format!("<Channel id={} name={}>", self.id, self.name)
    }

    pub fn __repr__(&self) -> String {
        format!(
            "Channel(id='{}', name='{}', channel_type={}, guild_id={})",
            self.id,
            self.name,
            self.channel_type,
            match &self.guild_id {
                Some(id) => format!("'{id}'"),
                None => "None".to_string(),
            }
        )
    }
}

impl Channel {
    pub fn from_json(data: Value) -> Self {
        serde_json::from_value(data).unwrap()
    }
}

/// Voice Connection to a Discord voice channel
#[pyclass]
#[derive(Clone)]
pub struct VoiceConnection {
    #[pyo3(get)]
    pub guild_id: String,
    #[pyo3(get)]
    pub channel_id: String,
    #[pyo3(get)]
    pub session_id: String,
    #[pyo3(get)]
    pub token: String,
    #[pyo3(get)]
    pub endpoint: String,
    #[pyo3(get)]
    pub connected: bool,
    #[pyo3(get)]
    pub self_mute: bool,
    #[pyo3(get)]
    pub self_deaf: bool,
}

#[pymethods]
impl VoiceConnection {
    #[new]
    pub const fn new(
        guild_id: String,
        channel_id: String,
        session_id: String,
        token: String,
        endpoint: String,
        self_mute: bool,
        self_deaf: bool,
    ) -> Self {
        Self {
            guild_id,
            channel_id,
            session_id,
            token,
            endpoint,
            connected: false,
            self_mute,
            self_deaf,
        }
    }

    pub fn __str__(&self) -> String {
        format!(
            "<VoiceConnection guild_id={} channel_id={} connected={}>",
            self.guild_id, self.channel_id, self.connected
        )
    }

    pub fn __repr__(&self) -> String {
        format!(
            "VoiceConnection(guild_id='{}', channel_id='{}', connected={})",
            self.guild_id, self.channel_id, self.connected
        )
    }

    /// Connect to the voice channel
    pub fn connect(&mut self) {
        // In a real implementation, this would establish a WebSocket connection
        // to the Discord voice server using the token and endpoint
        self.connected = true;
    }

    /// Disconnect from the voice channel
    pub fn disconnect(&mut self) {
        // In a real implementation, this would close the WebSocket connection
        self.connected = false;
    }

    /// Set self mute status
    pub fn set_self_mute(&mut self, mute: bool) {
        self.self_mute = mute;
    }

    /// Set self deaf status
    pub fn set_self_deaf(&mut self, deaf: bool) {
        self.self_deaf = deaf;
    }
}

/// Audio player for Discord voice connections
#[pyclass]
#[derive(Default)]
pub struct AudioPlayer {
    connection: Option<VoiceConnection>,
    playing: bool,
    paused: bool,
    volume: f32,
}

#[pymethods]
impl AudioPlayer {
    #[new]
    pub fn new() -> Self {
        Self::default()
    }

    pub fn __str__(&self) -> String {
        format!(
            "<AudioPlayer playing={} paused={} volume={}>",
            self.playing, self.paused, self.volume
        )
    }

    /// Attach to a voice connection
    pub fn attach(&mut self, connection: VoiceConnection) {
        self.connection = Some(connection);
    }

    /// Start playing audio from a file
    pub fn play_file(&mut self, _file_path: String) -> bool {
        if self.connection.is_none() {
            return false;
        }

        if let Some(conn) = &self.connection {
            if !conn.connected {
                return false;
            }
        }

        // In a real implementation, this would read the audio file and send
        // the audio data to the Discord voice connection
        self.playing = true;
        self.paused = false;

        true
    }

    /// Stop playing audio
    pub fn stop(&mut self) {
        self.playing = false;
        self.paused = false;
    }

    /// Pause audio playback
    pub fn pause(&mut self) {
        if self.playing {
            self.paused = true;
        }
    }

    /// Resume audio playback
    pub fn resume(&mut self) {
        if self.playing && self.paused {
            self.paused = false;
        }
    }

    /// Set the volume (0.0 to 2.0)
    pub fn set_volume(&mut self, volume: f32) -> PyResult<()> {
        if !(0.0..=2.0).contains(&volume) {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "Volume must be between 0.0 and 2.0",
            ));
        }
        self.volume = volume;
        Ok(())
    }

    /// Get the current playback status
    #[getter]
    pub const fn is_playing(&self) -> bool {
        self.playing && !self.paused
    }

    /// Get the current pause status
    #[getter]
    pub const fn is_paused(&self) -> bool {
        self.playing && self.paused
    }

    /// Get the current volume
    #[getter]
    pub const fn volume(&self) -> f32 {
        self.volume
    }
}

/// Discord Guild (Server) model
#[pyclass]
#[derive(Clone, Deserialize)]
pub struct Guild {
    #[pyo3(get)]
    #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
    pub id: String,
    #[pyo3(get)]
    #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
    pub name: String,
    #[pyo3(get)]
    #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
    pub owner_id: String,
}

#[pymethods]
impl Guild {
    #[new]
    pub const fn new(id: String, name: String, owner_id: String) -> Self {
        Self { id, name, owner_id }
    }

    pub fn __str__(&self) -> String {
        format!("<Guild id={} name={}>", self.id, self.name)
    }

    pub fn __repr__(&self) -> String {
        format!(
            "Guild(id='{}', name='{}', owner_id='{}')",
            self.id, self.name, self.owner_id
        )
    }
}

impl Guild {
    pub fn from_json(data: Value) -> Self {
        serde_json::from_value(data).unwrap()
    }
}
