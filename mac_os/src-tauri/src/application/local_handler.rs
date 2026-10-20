use crate::commons::{Command, Result};
use crate::modules::{
    audio::application::{AudioSessions, VoiceSelection},
    diagnostics::application::StorageCheck,
    operations::application::{CommandHandler, Completion},
    personal_voice::application::{RegistrationTarget, VoiceRegistration},
};
use std::sync::{Arc, atomic::AtomicBool};
pub(crate) struct LocalHandler {
    pub checker: Arc<dyn StorageCheck>,
    pub registration: VoiceRegistration,
    pub sessions: AudioSessions,
}
impl CommandHandler for LocalHandler {
    fn execute(
        &self,
        command: Command,
        cancelled: Arc<AtomicBool>,
        progress: &dyn Fn(&str) -> Result<()>,
    ) -> Result<Completion> {
        match command {
            Command::CheckStorage => self.checker.check().map(Into::into),
            Command::EnrollVoice { input_id } => self.registration.execute(
                &input_id,
                RegistrationTarget::Legacy,
                cancelled,
                progress,
            ),
            Command::EnrollVoiceProfile {
                input_id,
                profile_id,
                name,
                replace,
            } => self.registration.execute(
                &input_id,
                RegistrationTarget::Named {
                    id: profile_id,
                    name,
                    replace,
                },
                cancelled,
                progress,
            ),
            Command::StartAudio {
                input_id,
                personal_voice,
            } => {
                let voice = if personal_voice {
                    VoiceSelection::Default
                } else {
                    VoiceSelection::Disabled
                };
                self.sessions.start(&input_id, voice, cancelled, progress)
            }
            Command::StartVoiceProfileAudio {
                input_id,
                voice_profile_id,
            } => self.sessions.start(
                &input_id,
                VoiceSelection::Named(voice_profile_id),
                cancelled,
                progress,
            ),
        }
    }
}
