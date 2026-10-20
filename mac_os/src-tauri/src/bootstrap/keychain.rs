#[cfg(target_os = "macos")]
pub(super) fn database_key(existing: bool) -> Result<String, Box<dyn std::error::Error>> {
    use security_framework::passwords::{get_generic_password, set_generic_password};
    let service = "com.dotfiles.microphone.local.sqlcipher";
    let account = "database-v1";
    match get_generic_password(service, account) {
        Ok(key) => Ok(String::from_utf8(key)?),
        Err(error) if error.code() == -25300 && !existing => {
            let key = format!(
                "{}{}",
                uuid::Uuid::new_v4().simple(),
                uuid::Uuid::new_v4().simple()
            );
            set_generic_password(service, account, key.as_bytes())?;
            Ok(key)
        }
        Err(error) => Err(Box::new(error)),
    }
}
#[cfg(not(target_os = "macos"))]
pub(super) fn database_key(_: bool) -> Result<String, Box<dyn std::error::Error>> {
    Err("Local service currently supports macOS only".into())
}
