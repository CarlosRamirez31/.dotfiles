use serde::Deserialize;
use std::path::Path;
use tracing_subscriber::{filter::Targets, prelude::*};

/// Only our own structured events are enabled; provider debug logs may contain sensitive data.
pub fn initialize(
    directory: &Path,
    component: &str,
) -> Result<tracing_appender::non_blocking::WorkerGuard, Box<dyn std::error::Error>> {
    std::fs::create_dir_all(directory)?;
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        std::fs::set_permissions(directory, std::fs::Permissions::from_mode(0o700))?;
    }
    let file = tracing_appender::rolling::Builder::new()
        .rotation(tracing_appender::rolling::Rotation::DAILY)
        .filename_prefix(component)
        .filename_suffix("jsonl")
        .max_log_files(7)
        .build(directory)?;
    let (writer, guard) = tracing_appender::non_blocking::NonBlockingBuilder::default()
        .buffered_lines_limit(256)
        .lossy(true)
        .finish(file);
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::fmt::layer()
                .json()
                .with_ansi(false)
                .with_writer(writer)
                .with_filter(Targets::new().with_target("mac_os_lib", tracing::Level::INFO)),
        )
        .try_init()?;
    tracing::info!(event = "process.started", component);
    Ok(guard)
}

/// The UI cannot submit free text, request bodies, tokens or arbitrary metadata to the log file.
#[derive(Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ClientEvent {
    Connected,
    RequestAccepted,
    ConnectionLost,
    RequestFailed,
    StartupFailed,
}
impl ClientEvent {
    pub fn code(&self) -> &'static str {
        match self {
            Self::RequestAccepted => "client.request_accepted",
            Self::Connected => "client.connected",
            Self::ConnectionLost => "client.connection_lost",
            Self::RequestFailed => "client.request_failed",
            Self::StartupFailed => "client.startup_failed",
        }
    }
}
#[tauri::command]
pub fn client_log(event: ClientEvent, operation_id: Option<String>) -> Result<(), String> {
    let operation_id = operation_id
        .map(|id| uuid::Uuid::parse_str(&id).map(|id| id.to_string()))
        .transpose()
        .map_err(|_| "invalid_log_correlation")?;
    match event {
        ClientEvent::Connected | ClientEvent::RequestAccepted => {
            tracing::info!(source = "client", event = event.code(), operation_id)
        }
        ClientEvent::ConnectionLost => {
            tracing::warn!(source = "client", event = event.code(), operation_id)
        }
        ClientEvent::RequestFailed | ClientEvent::StartupFailed => {
            tracing::error!(source = "client", event = event.code(), operation_id)
        }
    }
    Ok(())
}
