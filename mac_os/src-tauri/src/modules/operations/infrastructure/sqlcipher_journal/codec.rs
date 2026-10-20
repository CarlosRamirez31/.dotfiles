use crate::commons::{Error, Result};

pub(super) fn decode<T: serde::de::DeserializeOwned>(value: String) -> Result<T> {
    serde_json::from_str(&value).map_err(|_| Error::Storage)
}
pub(super) fn encode(value: &impl serde::Serialize) -> Result<String> {
    serde_json::to_string(value).map_err(|_| Error::Storage)
}
