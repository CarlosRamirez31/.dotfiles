use crate::modules::audio::domain::capability::{
    CapabilityError as Error, CapabilityResult as Result,
};
pub(super) const STREAM_MODE: &str = "stream";
pub(super) const ENROLL_MODE: &str = "enroll";
const PROTOCOL_VERSION: i64 = 1;
pub(super) fn response(line: &str) -> Result<serde_json::Value> {
    let result: serde_json::Value =
        serde_json::from_str(line).map_err(|_| Error::InvalidResponse)?;
    if result.get("error").is_some() {
        let code = result
            .get("error")
            .cloned()
            .and_then(|value| serde_json::from_value::<WorkerError>(value).ok());
        return Err(match code {
            Some(WorkerError::InvalidInput) => Error::InvalidInput,
            Some(WorkerError::InvalidResponse) => Error::InvalidResponse,
            Some(WorkerError::Unavailable) => Error::Unavailable,
            Some(WorkerError::Timeout) => Error::Timeout,
            Some(WorkerError::Cancelled) => Error::Cancelled,
            _ => Error::InferenceFailed,
        });
    }
    Ok(result)
}

pub(super) fn ready(ready: &serde_json::Value) -> Result<()> {
    if ready.get("ready").and_then(|v| v.as_bool()) != Some(true)
        || ready.get("protocol").and_then(|v| v.as_i64()) != Some(PROTOCOL_VERSION)
    {
        return Err(Error::Unavailable);
    }
    Ok(())
}

pub(super) fn embedding(reply: serde_json::Value) -> Result<Vec<f32>> {
    let embedding: Vec<f32> = serde_json::from_value(
        reply
            .get("embedding")
            .cloned()
            .ok_or(Error::InvalidResponse)?,
    )
    .map_err(|_| Error::InvalidResponse)?;
    if embedding.len() != 192 || embedding.iter().any(|v| !v.is_finite()) {
        return Err(Error::InvalidResponse);
    }
    Ok(embedding)
}

pub(super) fn probability(reply: serde_json::Value) -> Result<f32> {
    let probability = reply
        .get("probability")
        .and_then(|v| v.as_f64())
        .ok_or(Error::InvalidResponse)? as f32;
    if !probability.is_finite() || !(0.0..=1.0).contains(&probability) {
        return Err(Error::InvalidResponse);
    }
    Ok(probability)
}
#[derive(serde::Deserialize)]
#[serde(rename_all = "snake_case")]
enum WorkerError {
    InvalidInput,
    InvalidResponse,
    Unavailable,
    Timeout,
    Cancelled,
}
