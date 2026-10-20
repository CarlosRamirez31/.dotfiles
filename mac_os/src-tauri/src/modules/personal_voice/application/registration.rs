use super::{EnrollmentFactory, VoiceProfiles};
use crate::commons::{AudioErrorCode, Error, Result};
use crate::modules::{audio::application::AudioCapture, operations::application::Completion};
use std::sync::{
    Arc,
    atomic::{AtomicBool, Ordering},
};
pub enum RegistrationTarget {
    Legacy,
    Named {
        id: String,
        name: String,
        replace: bool,
    },
}
pub struct VoiceRegistration {
    pub profiles: Arc<dyn VoiceProfiles>,
    pub factory: Arc<dyn EnrollmentFactory>,
    pub capture: Arc<dyn AudioCapture>,
}
impl VoiceRegistration {
    pub fn execute(
        &self,
        input: &str,
        target: RegistrationTarget,
        cancelled: Arc<AtomicBool>,
        progress: &dyn Fn(&str) -> Result<()>,
    ) -> Result<Completion> {
        if let RegistrationTarget::Named { id, replace, .. } = &target {
            let existing = self.profiles.list()?;
            let exists = existing.iter().any(|profile| &profile.id == id);
            if *replace && !exists {
                return Err(Error::NotFound);
            }
            if !replace && exists {
                return Err(Error::Conflict);
            }
        }
        progress("preparing_voice_model")?;
        let mut enrollment = self.factory.prepare_enrollment(cancelled.clone())?;
        progress("recording_enrollment_10_seconds")?;
        let pcm = self.capture.enroll(input, cancelled.clone())?;
        progress("creating_voice_profile")?;
        let embedding = enrollment.enroll(&pcm)?;
        if cancelled.load(Ordering::Acquire) {
            return Err(Error::Audio(AudioErrorCode::EnrollmentCancelled));
        }
        match target {
            RegistrationTarget::Legacy => self.profiles.save(&embedding)?,
            RegistrationTarget::Named { id, name, replace } => self
                .profiles
                .save_profile(&id, &name, &embedding, replace)?,
        }
        Ok(Completion {
            detail: "voice_enrolled".into(),
            effect_committed: true,
        })
    }
}
