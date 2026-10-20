use serde::{Deserialize, Serialize};
/// Requests work; events describe a transition already committed.
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(tag = "type", rename_all = "snake_case", deny_unknown_fields)]
pub enum Command {
    CheckStorage,
    StartAudio {
        input_id: String,
        personal_voice: bool,
    },
    StartVoiceProfileAudio {
        input_id: String,
        voice_profile_id: String,
    },
    EnrollVoiceProfile {
        input_id: String,
        profile_id: String,
        name: String,
        replace: bool,
    },
    EnrollVoice {
        input_id: String,
    },
}
impl Command {
    pub fn kind(&self) -> crate::modules::operations::domain::OperationKind {
        use crate::modules::operations::domain::OperationKind;
        match self {
            Self::CheckStorage => OperationKind::StorageCheck,
            Self::StartAudio { .. } | Self::StartVoiceProfileAudio { .. } => {
                OperationKind::AudioStart
            }
            Self::EnrollVoice { .. } | Self::EnrollVoiceProfile { .. } => {
                OperationKind::VoiceEnrollment
            }
        }
    }
}
