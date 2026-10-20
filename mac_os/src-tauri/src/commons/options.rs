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
    #[serde(default = "default_shutdown_seconds")]
    pub shutdown_seconds: u64,
    #[serde(default = "super::protocol::default_api_version")]
    pub api_version: String,
    pub reconnect_ms: u64,
}
impl Default for Options {
    fn default() -> Self {
        Self {
            logging: LoggingOptions::default(),
            operations: Default::default(),
            voice: Default::default(),
            startup_seconds: 30,
            shutdown_seconds: default_shutdown_seconds(),
            reconnect_ms: 1500,
            api_version: super::protocol::default_api_version(),
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
                environment_keys::API_VERSION => result.api_version = value,
                environment_keys::ENV_FILE => {}
                environment_keys::LOG_RETENTION_DAYS => result.logging.retention_days = number()?,
                environment_keys::LOG_CLEANUP_SECONDS => result.logging.cleanup_seconds = number()?,
                environment_keys::MAX_PENDING => {
                    result.operations.max_pending =
                        number()?.try_into().map_err(|_| "invalid_pending")?
                }
                environment_keys::MAX_OPERATIONS => {
                    result.operations.max_operations =
                        number()?.try_into().map_err(|_| "invalid_capacity")?
                }
                environment_keys::EVENT_BATCH => {
                    result.operations.event_batch =
                        number()?.try_into().map_err(|_| "invalid_batch")?
                }
                environment_keys::MAX_VOICE_PROFILES => {
                    result.voice.max_profiles = number()?
                        .try_into()
                        .map_err(|_| "invalid_profile_capacity")?
                }
                environment_keys::MODEL_LOAD_SECONDS => result.voice.load_seconds = number()?,
                environment_keys::INFERENCE_SECONDS => result.voice.inference_seconds = number()?,
                environment_keys::ENROLL_SECONDS => result.voice.enroll_seconds = number()?,
                environment_keys::VOICE_THRESHOLD => {
                    result.voice.threshold = value.parse().map_err(|_| "invalid_threshold")?
                }
                environment_keys::VOICE_RUNTIME => {
                    let path = PathBuf::from(value);
                    if !path.is_absolute() {
                        return Err("runtime_path_must_be_absolute".into());
                    }
                    result.voice.runtime = Some(path);
                }
                environment_keys::STARTUP_SECONDS => result.startup_seconds = number()?,
                environment_keys::SHUTDOWN_SECONDS => result.shutdown_seconds = number()?,
                environment_keys::SSE_RECONNECT_MS => result.reconnect_ms = number()?,
                _ => return Err(format!("unknown_option:{key}")),
            }
        }
        result.validate()?;
        Ok(result)
    }
    pub fn validate(&self) -> Result<(), String> {
        if !super::protocol::valid_api_version(&self.api_version)
            || !(1..=365).contains(&self.logging.retention_days)
            || !(60..=86400).contains(&self.logging.cleanup_seconds)
            || !(1..=128).contains(&self.operations.max_pending)
            || !(100..=100000).contains(&self.operations.max_operations)
            || self.operations.max_pending > self.operations.max_operations
            || !(1..=1024).contains(&self.operations.event_batch)
            || !(1..=128).contains(&self.voice.max_profiles)
            || !(1..=600).contains(&self.voice.load_seconds)
            || !(1..=30).contains(&self.voice.inference_seconds)
            || !(1..=300).contains(&self.voice.enroll_seconds)
            || !self.voice.threshold.is_finite()
            || !(0.0..=1.0).contains(&self.voice.threshold)
            || !(1..=300).contains(&self.startup_seconds)
            || !(1..=30).contains(&self.shutdown_seconds)
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

fn default_shutdown_seconds() -> u64 {
    5
}

mod environment_keys {
    pub const ENV_FILE: &str = "MIC_ENV_FILE";
    pub const LOG_RETENTION_DAYS: &str = "MIC_LOG_RETENTION_DAYS";
    pub const LOG_CLEANUP_SECONDS: &str = "MIC_LOG_CLEANUP_SECONDS";
    pub const MAX_PENDING: &str = "MIC_MAX_PENDING";
    pub const MAX_OPERATIONS: &str = "MIC_MAX_OPERATIONS";
    pub const EVENT_BATCH: &str = "MIC_EVENT_BATCH";
    pub const MAX_VOICE_PROFILES: &str = "MIC_MAX_VOICE_PROFILES";
    pub const MODEL_LOAD_SECONDS: &str = "MIC_MODEL_LOAD_SECONDS";
    pub const INFERENCE_SECONDS: &str = "MIC_INFERENCE_SECONDS";
    pub const ENROLL_SECONDS: &str = "MIC_ENROLL_SECONDS";
    pub const VOICE_THRESHOLD: &str = "MIC_VOICE_THRESHOLD";
    pub const VOICE_RUNTIME: &str = "MIC_VOICE_RUNTIME";
    pub const STARTUP_SECONDS: &str = "MIC_STARTUP_SECONDS";
    pub const SHUTDOWN_SECONDS: &str = "MIC_SHUTDOWN_SECONDS";
    pub const SSE_RECONNECT_MS: &str = "MIC_SSE_RECONNECT_MS";
    pub const API_VERSION: &str = "MIC_API_VERSION";
}
