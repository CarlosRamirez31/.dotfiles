mod capture;
mod config;
mod output;
use crate::commons::{AudioErrorCode, Error, Result};
use crate::modules::audio::{
    application::{AudioPipeline, NoiseReducer, PersonalVoice, cancelled},
    domain::Downsample,
};
use capture::Capture;
use output::Output;
use std::sync::{
    Arc,
    atomic::{AtomicBool, Ordering},
};
pub fn enroll(input_id: &str, stop: Arc<AtomicBool>) -> Result<Vec<f32>> {
    let mut capture = Capture::open(input_id, stop.clone())?;
    let mut downsample = Downsample::default();
    let mut samples = Vec::with_capacity(160_000);
    while samples.len() < 160_000 {
        let frame = capture
            .next(&stop)?
            .ok_or(Error::Audio(AudioErrorCode::EnrollmentCancelled))?;
        downsample.process(&frame, &mut samples);
    }
    let energy = samples.iter().map(|x| x * x).sum::<f32>() / samples.len() as f32;
    if energy < 0.00001 {
        return Err(Error::Audio(AudioErrorCode::EnrollmentTooQuiet));
    }
    Ok(samples)
}

pub fn run(
    input_id: &str,
    stop: Arc<AtomicBool>,
    personal: Option<Box<dyn PersonalVoice>>,
    noise: Box<dyn NoiseReducer>,
    progress: &dyn Fn(&str) -> Result<()>,
    voice_threshold: f32,
) -> Result<String> {
    if cancelled(&stop) {
        return Ok("cancelled".into());
    }
    let mut output = Output::open(stop.clone())?;
    let mut capture = Capture::open(input_id, stop.clone())?;
    progress("audio_active")?;
    let mut pipeline = AudioPipeline::new(personal, noise, voice_threshold);
    let result = (|| {
        while let Some(input) = capture.next(&stop)? {
            output.check()?;
            pipeline.process(&input, &stop, &mut |frame| output.push(frame))?;
        }
        Ok("audio_stopped".into())
    })();
    stop.store(true, Ordering::Release);
    drop(capture);
    drop(output);
    result
}
pub(super) const VIRTUAL_DEVICE_NAME: &str = "BlackHole 2ch";
const VIRTUAL_DEVICE_PREFIX: &str = "BlackHole";
