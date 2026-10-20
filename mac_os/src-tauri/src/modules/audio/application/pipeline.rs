use super::{NoiseReducer, PersonalVoice, cancelled};
use crate::commons::{AudioErrorCode, Error, Result};
use crate::modules::audio::domain::{Downsample, FRAME, PcmFrame};
use std::sync::{Arc, atomic::AtomicBool};

/// Stateful frame processing, independent of devices and transport callbacks.
pub struct AudioPipeline {
    personal: Option<Box<dyn PersonalVoice>>,
    noise: Box<dyn NoiseReducer>,
    threshold: f32,
    downsample: Downsample,
    input16: Vec<f32>,
    pending: Vec<PcmFrame>,
}
impl AudioPipeline {
    pub fn new(
        personal: Option<Box<dyn PersonalVoice>>,
        noise: Box<dyn NoiseReducer>,
        threshold: f32,
    ) -> Self {
        Self {
            personal,
            noise,
            threshold,
            downsample: Downsample::default(),
            input16: Vec::with_capacity(2560),
            pending: Vec::with_capacity(16),
        }
    }
    pub fn process(
        &mut self,
        input: &PcmFrame,
        stop: &Arc<AtomicBool>,
        emit: &mut dyn FnMut(PcmFrame) -> Result<()>,
    ) -> Result<()> {
        let mut filtered = [0.0; FRAME];
        self.noise
            .process(input, &mut filtered)
            .map_err(|_| Error::Audio(AudioErrorCode::NoiseProcessingFailed))?;
        let Some(voice) = self.personal.as_mut() else {
            return emit(filtered);
        };
        self.downsample.process(input, &mut self.input16);
        self.pending.push(filtered);
        if self.input16.len() < 2560 {
            return Ok(());
        }
        let probability = voice.probability(&self.input16)?;
        if cancelled(stop) {
            return Ok(());
        }
        for mut frame in self.pending.drain(..) {
            if probability < self.threshold {
                frame.fill(0.0);
            }
            emit(frame)?;
        }
        self.input16.clear();
        Ok(())
    }
}
