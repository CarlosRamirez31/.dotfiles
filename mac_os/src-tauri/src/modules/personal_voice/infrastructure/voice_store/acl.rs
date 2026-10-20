use crate::commons::{Error, Result};
pub(super) fn decode(document: String) -> Result<Vec<f32>> {
    let value: Vec<f32> = serde_json::from_str(&document).map_err(|_| Error::Storage)?;
    if value.len() != 192 || value.iter().any(|x| !x.is_finite()) {
        return Err(Error::Storage);
    }
    Ok(value)
}
