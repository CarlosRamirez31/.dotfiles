use super::core_audio;
use crate::{
    commons::Result,
    modules::audio::application::{AudioCapture, AudioPlayback, NoiseReducer, PersonalVoice},
};
use std::sync::{Arc, atomic::AtomicBool};
pub struct CoreAudioRuntime;
impl AudioCapture for CoreAudioRuntime {
    fn enroll(&self, input: &str, cancelled: Arc<AtomicBool>) -> Result<Vec<f32>> {
        core_audio::enroll(input, cancelled)
    }
}
impl AudioPlayback for CoreAudioRuntime {
    fn run(
        &self,
        input: &str,
        cancelled: Arc<AtomicBool>,
        personal: Option<Box<dyn PersonalVoice>>,
        noise: Box<dyn NoiseReducer>,
        progress: &dyn Fn(&str) -> Result<()>,
        threshold: f32,
    ) -> Result<String> {
        core_audio::run(input, cancelled, personal, noise, progress, threshold)
    }
}
