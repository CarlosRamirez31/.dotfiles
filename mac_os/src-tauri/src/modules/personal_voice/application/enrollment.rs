use crate::modules::audio::domain::capability::CapabilityResult;
use std::sync::{Arc, atomic::AtomicBool};

/// A prepared model session. Input is mono PCM at 16 kHz; output is the application voice embedding.
pub trait EnrollmentSession: Send {
    fn enroll(&mut self, pcm: &[f32]) -> CapabilityResult<Vec<f32>>;
}

/// Preparation must finish before recording. The returned session owns its resources until dropped.
pub trait EnrollmentFactory: Send + Sync {
    fn prepare_enrollment(
        &self,
        cancelled: Arc<AtomicBool>,
    ) -> CapabilityResult<Box<dyn EnrollmentSession>>;
}
