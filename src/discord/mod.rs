#![allow(unsafe_op_in_unsafe_fn)]

pub mod api;
pub mod errors;
pub mod gateway;
pub mod models;
pub(crate) mod util;

/// API version used for Discord API endpoints
pub const API_VERSION: u8 = 10;
/// Base URL for Discord API
pub const API_BASE_URL: &str = "https://discord.com/api";

macro_rules! url {
    ($e:literal) => {
        format!(concat!("{}/v{}", $e), crate::discord::API_BASE_URL, crate::discord::API_VERSION)
    };

    ($e:literal, $($rest:tt)*) => {
        format!(concat!("{}/v{}", $e), crate::discord::API_BASE_URL, crate::discord::API_VERSION, $($rest)*)
    };
}

pub(crate) use url;
