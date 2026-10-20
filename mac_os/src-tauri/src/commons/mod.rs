pub mod logging;
pub mod protocol;
use serde::{Deserialize, Serialize};

pub type Result<T> = std::result::Result<T, Error>;

#[derive(Debug)]
pub enum Error {
    Storage,
    Audio(AudioErrorCode),
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
    #[serde(default = "protocol::default_api_version")]
    pub api_version: String,
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

pub mod options;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum AudioErrorCode {
    AudioDeviceOrFormatUnavailable,
    AudioOutputBackpressure,
    AudioOverrunOrDeviceLost,
    Blackhole2chNotInstalled,
    BlackholeOutputFailed,
    ChooseAnotherDefaultVoice,
    EnrollmentCancelled,
    EnrollmentTooQuiet,
    MicrophoneTimeoutOrPermissionDenied,
    NoiseProcessingFailed,
    OperationCancelled,
    PersonalVoiceCancelled,
    PersonalVoiceInferenceFailed,
    PersonalVoiceInvalidInput,
    PersonalVoiceInvalidResponse,
    PersonalVoiceRuntimeNotInstalled,
    PersonalVoiceTimeout,
    RequiresFloat3248khzMonoOrStereo,
    VoiceEnrollmentRequired,
    VoiceProfileCapacity,
    VoiceSelectionRequired,
}
impl AudioErrorCode {
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::AudioDeviceOrFormatUnavailable => "audio_device_or_format_unavailable",
            Self::AudioOutputBackpressure => "audio_output_backpressure",
            Self::AudioOverrunOrDeviceLost => "audio_overrun_or_device_lost",
            Self::Blackhole2chNotInstalled => "blackhole_2ch_not_installed",
            Self::BlackholeOutputFailed => "blackhole_output_failed",
            Self::ChooseAnotherDefaultVoice => "choose_another_default_voice",
            Self::EnrollmentCancelled => "enrollment_cancelled",
            Self::EnrollmentTooQuiet => "enrollment_too_quiet",
            Self::MicrophoneTimeoutOrPermissionDenied => "microphone_timeout_or_permission_denied",
            Self::NoiseProcessingFailed => "noise_processing_failed",
            Self::OperationCancelled => "operation_cancelled",
            Self::PersonalVoiceCancelled => "personal_voice_cancelled",
            Self::PersonalVoiceInferenceFailed => "personal_voice_inference_failed",
            Self::PersonalVoiceInvalidInput => "personal_voice_invalid_input",
            Self::PersonalVoiceInvalidResponse => "personal_voice_invalid_response",
            Self::PersonalVoiceRuntimeNotInstalled => "personal_voice_runtime_not_installed",
            Self::PersonalVoiceTimeout => "personal_voice_timeout",
            Self::RequiresFloat3248khzMonoOrStereo => "requires_float32_48khz_mono_or_stereo",
            Self::VoiceEnrollmentRequired => "voice_enrollment_required",
            Self::VoiceProfileCapacity => "voice_profile_capacity",
            Self::VoiceSelectionRequired => "voice_selection_required",
        }
    }
}

pub mod utils;
