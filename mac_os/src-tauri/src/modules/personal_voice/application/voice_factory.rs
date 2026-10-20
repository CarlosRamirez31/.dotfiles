use crate::modules::audio::{application::PersonalVoice, domain::capability::CapabilityResult};
use std::sync::{Arc, atomic::AtomicBool};

pub trait PersonalVoiceFactory: Send + Sync {
    fn prepare_filter(
        &self,
        cancelled: Arc<AtomicBool>,
        embedding: &[f32],
    ) -> CapabilityResult<Box<dyn PersonalVoice>>;
}
