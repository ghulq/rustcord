mod discord;

use pyo3::prelude::*;

/// The Rust module for Discord API interactions
#[pymodule]
fn _rust(_py: Python, m: &PyModule) -> PyResult<()> {
    // API functionality
    m.add_class::<discord::api::DiscordClient>()?;
    m.add_class::<discord::models::Message>()?;
    m.add_class::<discord::models::User>()?;
    m.add_class::<discord::models::Channel>()?;
    m.add_class::<discord::models::Guild>()?;

    // Voice functionality
    m.add_class::<discord::models::VoiceState>()?;
    m.add_class::<discord::models::VoiceServerInfo>()?;
    m.add_class::<discord::models::VoiceConnection>()?;
    m.add_class::<discord::models::AudioPlayer>()?;

    // Gateway functionality
    m.add_class::<discord::gateway::GatewayClient>()?;

    // Error type
    m.add_class::<discord::errors::DiscordErrorPy>()?;

    // Version info
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;

    Ok(())
}
