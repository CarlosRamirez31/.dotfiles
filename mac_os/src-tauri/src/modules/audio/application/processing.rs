use crate::commons::{Error, Result};
pub use crate::modules::audio::domain::{FRAME, PcmFrame};
use std::sync::{
    Arc,
    atomic::{AtomicBool, Ordering},
};

pub trait NoiseReducer: Send {
    fn process(&mut self, input: &PcmFrame, output: &mut PcmFrame);
}

pub trait PersonalVoice: Send {
    fn probability(&mut self, pcm_16k: &[f32]) -> Result<f32>;
}

pub fn cancelled(flag: &Arc<AtomicBool>) -> bool {
    flag.load(Ordering::Acquire)
}
pub fn audio_error() -> Error {
    Error::Audio("audio_device_or_format_unavailable")
}
