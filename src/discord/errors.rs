use pyo3::prelude::*;
use pyo3::exceptions::{PyRuntimeError, PyConnectionError, PyValueError};
use pyo3::PyErr;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum DiscordError {
    #[error("API error: {0}")]
    ApiError(String),
    
    #[error("Invalid token: {0}")]
    InvalidToken(String),
    
    #[error("HTTP client error: {0}")]
    HttpClientError(String),
    
    #[error("Runtime error: {0}")]
    RuntimeError(String),
    
    #[error("Parse error: {0}")]
    ParseError(String),
    
    #[error("Connection error: {0}")]
    ConnectionError(String),
    
    #[error("Not connected: {0}")]
    NotConnected(String),
    
    #[error("Mutex error: {0}")]
    MutexError(String),
}

impl DiscordError {
    pub fn to_pyerr(&self) -> PyErr {
        match self {
            DiscordError::ApiError(msg) => PyRuntimeError::new_err(msg.clone()),
            DiscordError::InvalidToken(msg) => PyValueError::new_err(msg.clone()),
            DiscordError::HttpClientError(msg) => PyRuntimeError::new_err(msg.clone()),
            DiscordError::RuntimeError(msg) => PyRuntimeError::new_err(msg.clone()),
            DiscordError::ParseError(msg) => PyValueError::new_err(msg.clone()),
            DiscordError::ConnectionError(msg) => PyConnectionError::new_err(msg.clone()),
            DiscordError::NotConnected(msg) => PyRuntimeError::new_err(msg.clone()),
            DiscordError::MutexError(msg) => PyRuntimeError::new_err(msg.clone()),
        }
    }
}

/// Python-exposed Discord API error type
#[pyclass]
pub struct DiscordErrorPy {
    #[pyo3(get)]
    pub message: String,
    #[pyo3(get)]
    pub error_type: String,
}

#[pymethods]
impl DiscordErrorPy {
    #[new]
    pub fn new(message: String, error_type: String) -> Self {
        Self {
            message,
            error_type,
        }
    }
    
    pub fn __str__(&self) -> String {
        format!("DiscordError[{}]: {}", self.error_type, self.message)
    }
}
