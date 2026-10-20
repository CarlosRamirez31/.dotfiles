use super::{AudioPlayback, NoiseReducerFactory};
use crate::commons::Result;
use crate::modules::{
    operations::application::Completion,
    personal_voice::application::{PersonalVoiceFactory, VoiceProfiles},
};
use std::sync::{Arc, atomic::AtomicBool};
pub enum VoiceSelection {
    Disabled,
    Default,
    Named(String),
}
pub struct AudioSessions {
    pub profiles: Arc<dyn VoiceProfiles>,
    pub personal: Arc<dyn PersonalVoiceFactory>,
    pub playback: Arc<dyn AudioPlayback>,
    pub noise: Arc<dyn NoiseReducerFactory>,
    pub voice_threshold: f32,
}
impl AudioSessions {
    pub fn start(
        &self,
        input: &str,
        selected: VoiceSelection,
        cancelled: Arc<AtomicBool>,
        progress: &dyn Fn(&str) -> Result<()>,
    ) -> Result<Completion> {
        let personal = match selected {
            VoiceSelection::Disabled => None,
            selected => {
                progress("preparing_voice_model")?;
                let embedding = match selected {
                    VoiceSelection::Named(id) => self.profiles.embedding(&id)?,
                    VoiceSelection::Default => self.profiles.load()?,
                    VoiceSelection::Disabled => unreachable!(),
                };
                Some(
                    self.personal
                        .prepare_filter(cancelled.clone(), &embedding)?,
                )
            }
        };
        self.playback
            .run(
                input,
                cancelled,
                personal,
                self.noise.create(),
                progress,
                self.voice_threshold,
            )
            .map(Into::into)
    }
}
