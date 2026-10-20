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
            CapabilityError::InvalidInput => "personal_voice_invalid_input",
            CapabilityError::Unavailable => "personal_voice_runtime_not_installed",
            CapabilityError::Timeout => "personal_voice_timeout",
            CapabilityError::Cancelled => "personal_voice_cancelled",
            CapabilityError::InvalidResponse => "personal_voice_invalid_response",
            CapabilityError::InferenceFailed => "personal_voice_inference_failed",
        })
    }
}
