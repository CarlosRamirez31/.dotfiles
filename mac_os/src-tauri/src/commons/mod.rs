pub mod logging;
use serde::{Deserialize, Serialize};

pub type Result<T> = std::result::Result<T, Error>;

#[derive(Debug)]
pub enum Error {
    Storage,
    Audio(&'static str),
    NotFound,
    Conflict,
    Busy,
    Invalid,
    Capacity,
}

impl From<rusqlite::Error> for Error {
    fn from(_: rusqlite::Error) -> Self {
        Self::Storage
    }
}

#[derive(Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ConnectionInfo {
    pub endpoint: String,
    pub token: String,
    pub protocol_version: u32,
}

/// Requests work; events describe a transition already committed.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(tag = "type", rename_all = "snake_case", deny_unknown_fields)]
pub enum Command {
    CheckStorage,
    StartAudio {
        input_id: String,
        personal_voice: bool,
    },
    EnrollVoice {
        input_id: String,
    },
}
impl Command {
    pub fn kind(&self) -> &'static str {
        match self {
            Self::CheckStorage => "diagnostics.check_storage",
            Self::StartAudio { .. } => "audio.start",
            Self::EnrollVoice { .. } => "personal_voice.enroll",
        }
    }
}

pub mod options;
