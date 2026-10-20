#[derive(Debug, Clone, Copy, PartialEq)]
pub enum CapabilityError {
    InvalidInput,
    Unavailable,
    Timeout,
    Cancelled,
    InvalidResponse,
    InferenceFailed,
}
pub type CapabilityResult<T> = std::result::Result<T, CapabilityError>;
impl From<CapabilityError> for crate::commons::Error {
    fn from(error: CapabilityError) -> Self {
        Self::Audio(match error {
            CapabilityError::InvalidInput => {
                crate::commons::AudioErrorCode::PersonalVoiceInvalidInput
            }
            CapabilityError::Unavailable => {
                crate::commons::AudioErrorCode::PersonalVoiceRuntimeNotInstalled
            }
            CapabilityError::Timeout => crate::commons::AudioErrorCode::PersonalVoiceTimeout,
            CapabilityError::Cancelled => crate::commons::AudioErrorCode::PersonalVoiceCancelled,
            CapabilityError::InvalidResponse => {
                crate::commons::AudioErrorCode::PersonalVoiceInvalidResponse
            }
            CapabilityError::InferenceFailed => {
                crate::commons::AudioErrorCode::PersonalVoiceInferenceFailed
            }
        })
    }
}
