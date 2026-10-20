use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Status {
    Accepted,
    Running,
    CancellationRequested,
    Succeeded,
    Failed,
    Cancelled,
    Interrupted,
}
impl Status {
    pub fn terminal(self) -> bool {
        matches!(
            self,
            Self::Succeeded | Self::Failed | Self::Cancelled | Self::Interrupted
        )
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Operation {
    pub operation_id: String,
    pub kind: OperationKind,
    pub command: crate::commons::Command,
    pub status: Status,
    pub detail: Option<String>,
}

#[derive(Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Event {
    pub event_id: i64,
    pub event_type: String,
    pub schema_version: u32,
    pub module: String,
    pub operation_id: String,
    pub occurred_at_utc: String,
    pub operation: Operation,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub enum OperationKind {
    #[serde(rename = "diagnostics.check_storage")]
    StorageCheck,
    #[serde(rename = "audio.start")]
    AudioStart,
    #[serde(rename = "personal_voice.enroll")]
    VoiceEnrollment,
}
impl OperationKind {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::StorageCheck => "diagnostics.check_storage",
            Self::AudioStart => "audio.start",
            Self::VoiceEnrollment => "personal_voice.enroll",
        }
    }
}
impl std::fmt::Display for OperationKind {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        formatter.write_str(self.as_str())
    }
}
impl Status {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Accepted => "accepted",
            Self::Running => "running",
            Self::CancellationRequested => "cancellation_requested",
            Self::Succeeded => "succeeded",
            Self::Failed => "failed",
            Self::Cancelled => "cancelled",
            Self::Interrupted => "interrupted",
        }
    }
}
