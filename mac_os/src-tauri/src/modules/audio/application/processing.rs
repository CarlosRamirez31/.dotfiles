use crate::commons::AudioErrorCode;
use crate::commons::Error;
use crate::modules::audio::domain::capability::CapabilityResult;
pub use crate::modules::audio::domain::{FRAME, PcmFrame};
use std::sync::{
    Arc,
    atomic::{AtomicBool, Ordering},
};

pub trait NoiseReducer: Send {
    fn process(&mut self, input: &PcmFrame, output: &mut PcmFrame) -> CapabilityResult<()>;
}

pub trait PersonalVoice: Send {
    fn probability(&mut self, pcm_16k: &[f32]) -> CapabilityResult<f32>;
}

pub fn cancelled(flag: &Arc<AtomicBool>) -> bool {
    flag.load(Ordering::Acquire)
}
pub fn audio_error() -> Error {
    Error::Audio(AudioErrorCode::AudioDeviceOrFormatUnavailable)
}
