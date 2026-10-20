pub const LOCAL_SERVICE_MODE: &str = "--local-service";
pub const PROTOCOL_VERSION: u32 = 1;
pub const DEFAULT_API_VERSION: &str = "v1";
pub const TAURI_ORIGIN: &str = "tauri://localhost";
pub const TAURI_HTTP_ORIGIN: &str = "http://tauri.localhost";
pub const DEVELOPMENT_ORIGIN: &str = "http://localhost:1420";
pub fn default_api_version() -> String {
    DEFAULT_API_VERSION.into()
}
pub fn valid_api_version(value: &str) -> bool {
    let Some(digits) = value.strip_prefix('v') else {
        return false;
    };
    !digits.is_empty()
        && digits.len() <= 3
        && !digits.starts_with('0')
        && digits.bytes().all(|value| value.is_ascii_digit())
}
