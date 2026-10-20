use serde::Deserialize;
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
