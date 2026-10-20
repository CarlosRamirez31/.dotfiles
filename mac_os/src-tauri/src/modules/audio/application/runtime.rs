use super::{NoiseReducer, PersonalVoice};
use crate::commons::Result;
use std::sync::{Arc, atomic::AtomicBool};
pub trait AudioCapture: Send + Sync {
    fn enroll(&self, input: &str, cancelled: Arc<AtomicBool>) -> Result<Vec<f32>>;
}
pub trait AudioPlayback: Send + Sync {
    fn run(
        &self,
        input: &str,
        cancelled: Arc<AtomicBool>,
        personal: Option<Box<dyn PersonalVoice>>,
        noise: Box<dyn NoiseReducer>,
        progress: &dyn Fn(&str) -> Result<()>,
        threshold: f32,
    ) -> Result<String>;
}
pub trait NoiseReducerFactory: Send + Sync {
    fn create(&self) -> Box<dyn NoiseReducer>;
}
