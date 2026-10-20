use super::Supervisor;
use crate::commons::ConnectionInfo;
#[tauri::command]
pub fn local_connection(state: tauri::State<'_, Supervisor>) -> Result<ConnectionInfo, String> {
    state.connection()
}

#[tauri::command]
pub fn public_options(
    state: tauri::State<'_, Supervisor>,
) -> crate::commons::options::ClientOptions {
    crate::commons::options::ClientOptions {
        reconnect_ms: state.reconnect_ms,
    }
}
