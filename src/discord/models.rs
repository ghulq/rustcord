use pyo3::prelude::*;
use serde_json::Value;
use std::collections::HashMap;

/// Voice State model for Discord voice connections
#[pyclass]
#[derive(Clone)]
pub struct VoiceState {
    #[pyo3(get)]
    pub guild_id: Option<String>,
    #[pyo3(get)]
    pub channel_id: Option<String>,
    #[pyo3(get)]
    pub user_id: String,
    #[pyo3(get)]
    pub session_id: String,
    #[pyo3(get)]
    pub deaf: bool,
    #[pyo3(get)]
    pub mute: bool,
    #[pyo3(get)]
    pub self_deaf: bool,
    #[pyo3(get)]
    pub self_mute: bool,
    #[pyo3(get)]
    pub self_stream: bool,
    #[pyo3(get)]
    pub self_video: bool,
    #[pyo3(get)]
    pub suppress: bool,
}

#[pymethods]
impl VoiceState {
    #[new]
    pub fn new(
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
        format!("<VoiceState user_id={} channel_id={}>", 
            self.user_id, 
            match &self.channel_id {
                Some(id) => id,
                None => "None",
            }
        )
    }
    
    pub fn __repr__(&self) -> String {
        format!(
            "VoiceState(user_id='{}', session_id='{}', channel_id={}, guild_id={})",
            self.user_id,
            self.session_id,
            match &self.channel_id {
                Some(id) => format!("'{}'", id),
                None => "None".to_string(),
            },
            match &self.guild_id {
                Some(id) => format!("'{}'", id),
                None => "None".to_string(),
            }
        )
    }
}

impl VoiceState {
    pub fn from_json(data: Value) -> Self {
        let guild_id = data.get("guild_id")
            .and_then(|v| v.as_str())
            .map(|s| s.to_string());
            
        let channel_id = data.get("channel_id")
            .and_then(|v| v.as_str())
            .map(|s| s.to_string());
            
        let user_id = data.get("user_id")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string();
            
        let session_id = data.get("session_id")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string();
            
        let deaf = data.get("deaf")
            .and_then(|v| v.as_bool())
            .unwrap_or(false);
            
        let mute = data.get("mute")
            .and_then(|v| v.as_bool())
            .unwrap_or(false);
            
        let self_deaf = data.get("self_deaf")
            .and_then(|v| v.as_bool())
            .unwrap_or(false);
            
        let self_mute = data.get("self_mute")
            .and_then(|v| v.as_bool())
            .unwrap_or(false);
            
        let self_stream = data.get("self_stream")
            .and_then(|v| v.as_bool())
            .unwrap_or(false);
            
        let self_video = data.get("self_video")
            .and_then(|v| v.as_bool())
            .unwrap_or(false);
            
        let suppress = data.get("suppress")
            .and_then(|v| v.as_bool())
            .unwrap_or(false);
            
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
}

/// Voice Server information from Discord
#[pyclass]
#[derive(Clone)]
pub struct VoiceServerInfo {
    #[pyo3(get)]
    pub token: String,
    #[pyo3(get)]
    pub guild_id: String,
    #[pyo3(get)]
    pub endpoint: String,
}

#[pymethods]
impl VoiceServerInfo {
    #[new]
    pub fn new(token: String, guild_id: String, endpoint: String) -> Self {
        Self {
            token,
            guild_id,
            endpoint,
        }
    }
    
    pub fn __str__(&self) -> String {
        format!("<VoiceServerInfo guild_id={} endpoint={}>", self.guild_id, self.endpoint)
    }
    
    pub fn __repr__(&self) -> String {
        format!("VoiceServerInfo(token='{}', guild_id='{}', endpoint='{}')",
            self.token, self.guild_id, self.endpoint)
    }
}

impl VoiceServerInfo {
    pub fn from_json(data: Value) -> Self {
        let token = data.get("token")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string();
            
        let guild_id = data.get("guild_id")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string();
            
        let endpoint = data.get("endpoint")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string();
            
        Self {
            token,
            guild_id,
            endpoint,
        }
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
    pub fn new(id: String, channel_id: String, content: String, author_id: String, author_username: String) -> Self {
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
        format!("Message(id='{}', channel_id='{}', content='{}', author_id='{}', author_username='{}')",
            self.id, self.channel_id, self.content, self.author_id, self.author_username)
    }
}

impl Message {
    pub fn from_json(data: Value) -> Self {
        let id = data.get("id")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string();
            
        let channel_id = data.get("channel_id")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string();
            
        let content = data.get("content")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string();
            
        let author_id = data.get("author")
            .and_then(|v| v.get("id"))
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string();
            
        let author_username = data.get("author")
            .and_then(|v| v.get("username"))
            .and_then(|v| v.as_str())
            .unwrap_or("")
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
#[derive(Clone)]
pub struct User {
    #[pyo3(get)]
    pub id: String,
    #[pyo3(get)]
    pub username: String,
    #[pyo3(get)]
    pub discriminator: String,
    #[pyo3(get)]
    pub bot: bool,
}

#[pymethods]
impl User {
    #[new]
    pub fn new(id: String, username: String, discriminator: String, bot: bool) -> Self {
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
        format!("User(id='{}', username='{}', discriminator='{}', bot={})",
            self.id, self.username, self.discriminator, self.bot)
    }
}

impl User {
    pub fn from_json(data: Value) -> Self {
        let id = data.get("id")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string();
            
        let username = data.get("username")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string();
            
        let discriminator = data.get("discriminator")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string();
            
        let bot = data.get("bot")
            .and_then(|v| v.as_bool())
            .unwrap_or(false);
            
        Self {
            id,
            username,
            discriminator,
            bot,
        }
    }
}

/// Discord Channel model
#[pyclass]
#[derive(Clone)]
pub struct Channel {
    #[pyo3(get)]
    pub id: String,
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub channel_type: u8,
    #[pyo3(get)]
    pub guild_id: Option<String>,
}

#[pymethods]
impl Channel {
    #[new]
    pub fn new(id: String, name: String, channel_type: u8, guild_id: Option<String>) -> Self {
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
        format!("Channel(id='{}', name='{}', channel_type={}, guild_id={})",
            self.id, self.name, self.channel_type, 
            match &self.guild_id {
                Some(id) => format!("'{}'", id),
                None => "None".to_string(),
            })
    }
}

impl Channel {
    pub fn from_json(data: Value) -> Self {
        let id = data.get("id")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string();
            
        let name = data.get("name")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string();
            
        let channel_type = data.get("type")
            .and_then(|v| v.as_u64())
            .unwrap_or(0) as u8;
            
        let guild_id = data.get("guild_id")
            .and_then(|v| v.as_str())
            .map(|s| s.to_string());
            
        Self {
            id,
            name,
            channel_type,
            guild_id,
        }
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
    pub fn new(
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
        format!("<VoiceConnection guild_id={} channel_id={} connected={}>", 
            self.guild_id, self.channel_id, self.connected)
    }
    
    pub fn __repr__(&self) -> String {
        format!(
            "VoiceConnection(guild_id='{}', channel_id='{}', connected={})",
            self.guild_id, 
            self.channel_id,
            self.connected
        )
    }
    
    /// Connect to the voice channel
    pub fn connect(&mut self) -> PyResult<()> {
        // In a real implementation, this would establish a WebSocket connection
        // to the Discord voice server using the token and endpoint
        self.connected = true;
        Ok(())
    }
    
    /// Disconnect from the voice channel
    pub fn disconnect(&mut self) -> PyResult<()> {
        // In a real implementation, this would close the WebSocket connection
        self.connected = false;
        Ok(())
    }
    
    /// Set self mute status
    pub fn set_self_mute(&mut self, mute: bool) -> PyResult<()> {
        self.self_mute = mute;
        Ok(())
    }
    
    /// Set self deaf status
    pub fn set_self_deaf(&mut self, deaf: bool) -> PyResult<()> {
        self.self_deaf = deaf;
        Ok(())
    }
}

/// Audio player for Discord voice connections
#[pyclass]
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
        Self {
            connection: None,
            playing: false,
            paused: false,
            volume: 1.0,
        }
    }
    
    pub fn __str__(&self) -> String {
        format!("<AudioPlayer playing={} paused={} volume={}>", 
            self.playing, self.paused, self.volume)
    }
    
    /// Attach to a voice connection
    pub fn attach(&mut self, connection: VoiceConnection) -> PyResult<()> {
        self.connection = Some(connection);
        Ok(())
    }
    
    /// Start playing audio from a file
    pub fn play_file(&mut self, file_path: String) -> PyResult<bool> {
        if self.connection.is_none() {
            return Ok(false);
        }
        
        if let Some(conn) = &self.connection {
            if !conn.connected {
                return Ok(false);
            }
        }
        
        // In a real implementation, this would read the audio file and send
        // the audio data to the Discord voice connection
        self.playing = true;
        self.paused = false;
        Ok(true)
    }
    
    /// Stop playing audio
    pub fn stop(&mut self) -> PyResult<()> {
        self.playing = false;
        self.paused = false;
        Ok(())
    }
    
    /// Pause audio playback
    pub fn pause(&mut self) -> PyResult<()> {
        if self.playing {
            self.paused = true;
        }
        Ok(())
    }
    
    /// Resume audio playback
    pub fn resume(&mut self) -> PyResult<()> {
        if self.playing && self.paused {
            self.paused = false;
        }
        Ok(())
    }
    
    /// Set the volume (0.0 to 2.0)
    pub fn set_volume(&mut self, volume: f32) -> PyResult<()> {
        if volume < 0.0 || volume > 2.0 {
            return Err(pyo3::exceptions::PyValueError::new_err("Volume must be between 0.0 and 2.0"));
        }
        self.volume = volume;
        Ok(())
    }
    
    /// Get the current playback status
    #[getter]
    pub fn is_playing(&self) -> bool {
        self.playing && !self.paused
    }
    
    /// Get the current pause status
    #[getter]
    pub fn is_paused(&self) -> bool {
        self.playing && self.paused
    }
    
    /// Get the current volume
    #[getter]
    pub fn volume(&self) -> f32 {
        self.volume
    }
}

/// Discord Guild (Server) model
#[pyclass]
#[derive(Clone)]
pub struct Guild {
    #[pyo3(get)]
    pub id: String,
    #[pyo3(get)]
    pub name: String,
    #[pyo3(get)]
    pub owner_id: String,
}

#[pymethods]
impl Guild {
    #[new]
    pub fn new(id: String, name: String, owner_id: String) -> Self {
        Self {
            id,
            name,
            owner_id,
        }
    }
    
    pub fn __str__(&self) -> String {
        format!("<Guild id={} name={}>", self.id, self.name)
    }
    
    pub fn __repr__(&self) -> String {
        format!("Guild(id='{}', name='{}', owner_id='{}')",
            self.id, self.name, self.owner_id)
    }
}

impl Guild {
    pub fn from_json(data: Value) -> Self {
        let id = data.get("id")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string();
            
        let name = data.get("name")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string();
            
        let owner_id = data.get("owner_id")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string();
            
        Self {
            id,
            name,
            owner_id,
        }
    }
}
