use super::util;
use pyo3::prelude::*;
use serde::{
    Deserialize, Deserializer,
    de::{MapAccess, Visitor},
};
use std::fmt;

util::py_getter_class! {
    /// Voice State model for Discord voice connections
    #[pyclass]
    #[derive(Clone, Deserialize)]
    pub struct VoiceState {
        #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
        pub user_id: String,
        #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
        pub session_id: String,
        #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
        pub guild_id: Option<String>,
        #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
        pub channel_id: Option<String>,
        #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
        pub deaf: bool,
        #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
        pub mute: bool,
        #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
        pub self_deaf: bool,
        #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
        pub self_mute: bool,
        #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
        pub self_stream: bool,
        #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
        pub self_video: bool,
        #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
        pub suppress: bool,
    }

    #[pymethods]
    impl VoiceState {
        pub fn __str__(&self) -> String {
            format!(
                "<VoiceState user_id={} channel_id={}>",
                self.user_id,
                self.channel_id.as_deref().unwrap_or("None"),
            )
        }
    }
}

util::py_getter_class! {
    /// Voice Server information from Discord
    #[pyclass]
    #[derive(Clone, Deserialize)]
    pub struct VoiceServerInfo {
        #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
        pub token: String,
        #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
        pub guild_id: String,
        #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
        pub endpoint: String,
    }

    #[pymethods]
    impl VoiceServerInfo {
        pub fn __str__(&self) -> String {
            format!(
                "<VoiceServerInfo guild_id={} endpoint={}>",
                self.guild_id, self.endpoint
            )
        }
    }
}

util::py_getter_class! {
    /// Discord Message model
    #[pyclass]
    #[derive(Clone, Default)]
    pub struct Message {
        pub id: String,
        pub channel_id: String,
        pub content: String,
        pub author_id: String,
        pub author_username: String,
    }

    #[pymethods]
    impl Message {
        pub fn __str__(&self) -> String {
            format!("<Message id={} content={}>", self.id, self.content)
        }
    }
}

impl<'de> Deserialize<'de> for Message {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: Deserializer<'de>,
    {
        deserializer.deserialize_map(MessageVisitor)
    }
}

#[derive(Deserialize)]
struct MessageAuthorIntermediate {
    #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
    id: String,

    #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
    username: String,
}

struct MessageVisitor;

impl<'de> Visitor<'de> for MessageVisitor {
    type Value = Message;

    fn expecting(&self, formatter: &mut fmt::Formatter) -> fmt::Result {
        formatter.write_str("a map representing a Message")
    }

    fn visit_map<M>(self, mut map: M) -> Result<Message, M::Error>
    where
        M: MapAccess<'de>,
    {
        let mut message = Message::default();

        while let Some(key) = map.next_key::<String>()? {
            match key.as_str() {
                "id" => {
                    if let Ok(new_id) = map.next_value::<String>() {
                        message.id = new_id;
                    }
                }
                "channel_id" => {
                    if let Ok(new_channel_id) = map.next_value::<String>() {
                        message.channel_id = new_channel_id;
                    }
                }
                "content" => {
                    if let Ok(new_content) = map.next_value::<String>() {
                        message.content = new_content;
                    }
                }
                "author" => {
                    if let Ok(a) = map.next_value::<MessageAuthorIntermediate>() {
                        message.author_id = a.id;
                        message.author_username = a.username;
                    }
                }
                _ => {
                    let _ = map.next_value::<serde::de::IgnoredAny>()?;
                }
            }
        }

        Ok(message)
    }
}

util::py_getter_class! {
    /// Discord User model
    #[pyclass]
    #[derive(Clone, Deserialize)]
    pub struct User {
        #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
        pub id: String,
        #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
        pub username: String,
        #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
        pub discriminator: String,
        #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
        pub bot: bool,
    }

    #[pymethods]
    impl User {
        pub fn __str__(&self) -> String {
            format!("<User id={} username={}>", self.id, self.username)
        }
    }
}

util::py_getter_class! {
    /// Discord Channel model
    #[pyclass]
    #[derive(Clone, Deserialize)]
    pub struct Channel {
        #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
        pub id: String,
        #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
        pub name: String,
        #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
        pub channel_type: u8,
        #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
        pub guild_id: Option<String>,
    }

    #[pymethods]
    impl Channel {
        pub fn __str__(&self) -> String {
            format!("<Channel id={} name={}>", self.id, self.name)
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

util::py_getter_class! {
    /// Discord Guild (Server) model
    #[pyclass]
    #[derive(Clone, Deserialize)]
    pub struct Guild {
        #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
        pub id: String,
        #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
        pub name: String,
        #[serde(default, deserialize_with = "util::deserialize_default_on_error")]
        pub owner_id: String,
    }

    #[pymethods]
    impl Guild {
        pub fn __str__(&self) -> String {
            format!("<Guild id={} name={}>", self.id, self.name)
        }
    }
}
