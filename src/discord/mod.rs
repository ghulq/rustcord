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
