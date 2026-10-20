use crate::commons::{Error, Result};
use serde::Serialize;
#[derive(Clone, Debug, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct VoiceProfile {
    pub id: String,
    pub name: String,
    pub is_default: bool,
    pub updated_at: String,
}
pub fn validate(id: &str, name: &str) -> Result<()> {
    if uuid::Uuid::parse_str(id).is_err()
        || name.trim().is_empty()
        || name.chars().count() > 80
        || name.chars().any(char::is_control)
    {
        return Err(Error::Invalid);
    }
    Ok(())
}
