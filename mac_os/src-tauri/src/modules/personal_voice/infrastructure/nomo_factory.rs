use super::nomo_worker::NomoWorker;
use crate::modules::{
    audio::{application::PersonalVoice, domain::capability::CapabilityResult},
    personal_voice::{
        application::{EnrollmentFactory, EnrollmentSession, PersonalVoiceFactory},
        options::VoiceOptions,
    },
};
use std::{
    path::PathBuf,
    sync::{Arc, atomic::AtomicBool},
};

/// Keeps executable paths, provider selection and runtime options outside the command handler.
pub struct NomoFactory {
    runtime: PathBuf,
    script: PathBuf,
    options: VoiceOptions,
}
impl NomoFactory {
    pub fn new(runtime: PathBuf, script: PathBuf, options: VoiceOptions) -> Self {
        Self {
            runtime,
            script,
            options,
        }
    }
}
impl EnrollmentFactory for NomoFactory {
    fn prepare_enrollment(
        &self,
        cancelled: Arc<AtomicBool>,
    ) -> CapabilityResult<Box<dyn EnrollmentSession>> {
        Ok(Box::new(NomoWorker::start(
            &self.runtime,
            &self.script,
            cancelled,
            None,
            self.options.clone(),
        )?))
    }
}
impl PersonalVoiceFactory for NomoFactory {
    fn prepare_filter(
        &self,
        cancelled: Arc<AtomicBool>,
        embedding: &[f32],
    ) -> CapabilityResult<Box<dyn PersonalVoice>> {
        Ok(Box::new(NomoWorker::start(
            &self.runtime,
            &self.script,
            cancelled,
            Some(embedding),
            self.options.clone(),
        )?))
    }
}
