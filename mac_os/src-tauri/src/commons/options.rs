use serde::{Deserialize, Serialize};
use std::{
    collections::BTreeMap,
    path::{Path, PathBuf},
};
#[derive(Clone, Serialize, Deserialize)]
pub struct LoggingOptions {
    pub retention_days: u64,
    pub cleanup_seconds: u64,
}
impl Default for LoggingOptions {
    fn default() -> Self {
        Self {
            retention_days: 30,
            cleanup_seconds: 3600,
        }
    }
}
#[derive(Clone, Serialize, Deserialize)]
pub struct Options {
    pub logging: LoggingOptions,
    pub operations: crate::modules::operations::application::options::OperationsOptions,
    pub voice: crate::modules::personal_voice::options::VoiceOptions,
    pub startup_seconds: u64,
    pub reconnect_ms: u64,
}
impl Default for Options {
    fn default() -> Self {
        Self {
            logging: LoggingOptions::default(),
            operations: Default::default(),
            voice: Default::default(),
            startup_seconds: 30,
            reconnect_ms: 1500,
        }
    }
}
impl Options {
    pub fn load() -> Result<Self, String> {
        let path = std::env::var_os("MIC_ENV_FILE").map(PathBuf::from);
        let file = path
            .as_deref()
            .map(read_env)
            .transpose()?
            .unwrap_or_default();
        Self::from_values(
            file,
            std::env::vars()
                .filter(|(k, _)| k.starts_with("MIC_"))
                .collect(),
        )
    }
    pub fn from_values(
        mut file: BTreeMap<String, String>,
        environment: BTreeMap<String, String>,
    ) -> Result<Self, String> {
        file.extend(environment);
        let mut result = Self::default();
        for (key, value) in file {
            let number = || {
                value
                    .parse::<u64>()
                    .map_err(|_| format!("invalid_option:{key}"))
            };
            match key.as_str() {
                "MIC_ENV_FILE" => {}
                "MIC_LOG_RETENTION_DAYS" => result.logging.retention_days = number()?,
                "MIC_LOG_CLEANUP_SECONDS" => result.logging.cleanup_seconds = number()?,
                "MIC_MAX_PENDING" => {
                    result.operations.max_pending =
                        number()?.try_into().map_err(|_| "invalid_pending")?
                }
                "MIC_MAX_OPERATIONS" => {
                    result.operations.max_operations =
                        number()?.try_into().map_err(|_| "invalid_capacity")?
                }
                "MIC_EVENT_BATCH" => {
                    result.operations.event_batch =
                        number()?.try_into().map_err(|_| "invalid_batch")?
                }
                "MIC_MODEL_LOAD_SECONDS" => result.voice.load_seconds = number()?,
                "MIC_INFERENCE_SECONDS" => result.voice.inference_seconds = number()?,
                "MIC_ENROLL_SECONDS" => result.voice.enroll_seconds = number()?,
                "MIC_VOICE_THRESHOLD" => {
                    result.voice.threshold = value.parse().map_err(|_| "invalid_threshold")?
                }
                "MIC_VOICE_RUNTIME" => {
                    let path = PathBuf::from(value);
                    if !path.is_absolute() {
                        return Err("runtime_path_must_be_absolute".into());
                    }
                    result.voice.runtime = Some(path);
                }
                "MIC_STARTUP_SECONDS" => result.startup_seconds = number()?,
                "MIC_SSE_RECONNECT_MS" => result.reconnect_ms = number()?,
                _ => return Err(format!("unknown_option:{key}")),
            }
        }
        result.validate()?;
        Ok(result)
    }
    pub fn validate(&self) -> Result<(), String> {
        if !(1..=365).contains(&self.logging.retention_days)
            || !(60..=86400).contains(&self.logging.cleanup_seconds)
            || !(1..=128).contains(&self.operations.max_pending)
            || !(100..=100000).contains(&self.operations.max_operations)
            || self.operations.max_pending > self.operations.max_operations
            || !(1..=1024).contains(&self.operations.event_batch)
            || !(1..=600).contains(&self.voice.load_seconds)
            || !(1..=30).contains(&self.voice.inference_seconds)
            || !(1..=300).contains(&self.voice.enroll_seconds)
            || !self.voice.threshold.is_finite()
            || !(0.0..=1.0).contains(&self.voice.threshold)
            || !(1..=300).contains(&self.startup_seconds)
            || !(100..=30000).contains(&self.reconnect_ms)
        {
            return Err("option_out_of_range".into());
        }
        Ok(())
    }
}
pub(crate) fn read_env(path: &Path) -> Result<BTreeMap<String, String>, String> {
    // Explicit path only; no expansion, executable syntax or modification of global environment.
    let bytes = std::fs::read(path).map_err(|_| "env_file_unreadable")?;
    if bytes.len() > 65536 {
        return Err("env_file_too_large".into());
    }
    let text = String::from_utf8(bytes).map_err(|_| "invalid_env_encoding")?;
    let mut values = BTreeMap::new();
    for line in text
        .lines()
        .map(str::trim)
        .filter(|s| !s.is_empty() && !s.starts_with('#'))
    {
        let (key, value) = line.split_once('=').ok_or("invalid_env_assignment")?;
        let key = key.trim();
        let mut value = value.trim();
        if value.starts_with('\"') || value.starts_with('\'') {
            if value.len() < 2 || value.as_bytes().last() != value.as_bytes().first() {
                return Err("invalid_env_quotes".into());
            }
            value = &value[1..value.len() - 1];
        }
        if values.insert(key.to_owned(), value.to_owned()).is_some() {
            return Err("duplicate_env_option".into());
        }
    }
    Ok(values)
}

/// Public configuration allowlist; never includes runtime paths or credentials.
#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ClientOptions {
    pub reconnect_ms: u64,
}
