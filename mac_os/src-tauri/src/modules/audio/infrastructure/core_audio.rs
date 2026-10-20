use super::Downsample;
use crate::commons::{Error, Result};
use crate::modules::audio::application::{FRAME, PcmFrame, PersonalVoice, audio_error, cancelled};
use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use serde::Serialize;
use std::{
    sync::{
        Arc,
        atomic::{AtomicBool, Ordering},
    },
    time::{Duration, Instant},
};

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Devices {
    pub inputs: Vec<Input>,
    pub blackhole_available: bool,
}
#[derive(Serialize)]
pub struct Input {
    pub id: String,
    pub name: String,
}

pub fn devices() -> Result<Devices> {
    let host = cpal::default_host();
    let mut inputs = Vec::new();
    let mut blackhole_available = false;
    for device in host.devices().map_err(|_| audio_error())? {
        let description = device.description().map_err(|_| audio_error())?;
        let name = description.name().to_owned();
        if name == "BlackHole 2ch" {
            blackhole_available = device.supports_output();
        } else if device.supports_input() {
            inputs.push(Input {
                id: device.id().map_err(|_| audio_error())?.to_string(),
                name,
            });
        }
    }
    Ok(Devices {
        inputs,
        blackhole_available,
    })
}
fn config(device: &cpal::Device, input: bool) -> Result<cpal::StreamConfig> {
    let ranges: Vec<cpal::SupportedStreamConfigRange> = if input {
        device
            .supported_input_configs()
            .map_err(|_| audio_error())?
            .collect()
    } else {
        device
            .supported_output_configs()
            .map_err(|_| audio_error())?
            .collect()
    };
    let range = ranges
        .into_iter()
        .filter(|c| {
            c.sample_format() == cpal::SampleFormat::F32
                && c.min_sample_rate() <= 48000
                && c.max_sample_rate() >= 48000
                && c.channels() <= 2
        })
        .min_by_key(|c| c.channels())
        .ok_or(Error::Audio("requires_float32_48khz_mono_or_stereo"))?;
    Ok(range.with_sample_rate(48000).config())
}
struct Capture {
    _stream: cpal::Stream,
    frames: rtrb::Consumer<PcmFrame>,
    fault: Arc<AtomicBool>,
}
impl Capture {
    fn open(id: &str, stop: Arc<AtomicBool>) -> Result<Self> {
        let device = cpal::default_host()
            .device_by_id(&id.parse().map_err(|_| audio_error())?)
            .ok_or_else(audio_error)?;
        if device
            .description()
            .map_err(|_| audio_error())?
            .name()
            .contains("BlackHole")
        {
            return Err(Error::Invalid);
        }
        let config = config(&device, true)?;
        let channels = usize::from(config.channels);
        let (mut producer, consumer) = rtrb::RingBuffer::new(32);
        let fault = Arc::new(AtomicBool::new(false));
        let callback_fault = fault.clone();
        let error_fault = fault.clone();
        let mut frame = [0.0; FRAME];
        let mut position = 0;
        let stream = device
            .build_input_stream(
                config,
                move |input: &[f32], _| {
                    if stop.load(Ordering::Acquire) || callback_fault.load(Ordering::Relaxed) {
                        return;
                    }
                    for samples in input.chunks_exact(channels) {
                        frame[position] = samples.iter().sum::<f32>() / channels as f32;
                        position += 1;
                        if position == FRAME {
                            if producer.push(frame).is_err() {
                                callback_fault.store(true, Ordering::Release);
                                return;
                            }
                            position = 0;
                        }
                    }
                },
                move |_| {
                    error_fault.store(true, Ordering::Release);
                },
                None,
            )
            .map_err(|_| audio_error())?;
        stream.play().map_err(|_| audio_error())?;
        Ok(Self {
            _stream: stream,
            frames: consumer,
            fault,
        })
    }
    fn next(&mut self, stop: &Arc<AtomicBool>) -> Result<Option<PcmFrame>> {
        let deadline = Instant::now() + Duration::from_secs(3);
        loop {
            if cancelled(stop) {
                return Ok(None);
            }
            if self.fault.load(Ordering::Acquire) {
                return Err(Error::Audio("audio_overrun_or_device_lost"));
            }
            if let Ok(frame) = self.frames.pop() {
                return Ok(Some(frame));
            }
            if Instant::now() > deadline {
                return Err(Error::Audio("microphone_timeout_or_permission_denied"));
            }
            std::thread::sleep(Duration::from_millis(2));
        }
    }
}

pub fn enroll(input_id: &str, stop: Arc<AtomicBool>) -> Result<Vec<f32>> {
    let mut capture = Capture::open(input_id, stop.clone())?;
    let mut downsample = Downsample::default();
    let mut samples = Vec::with_capacity(160_000);
    while samples.len() < 160_000 {
        let frame = capture
            .next(&stop)?
            .ok_or(Error::Audio("enrollment_cancelled"))?;
        downsample.process(&frame, &mut samples);
    }
    let energy = samples.iter().map(|x| x * x).sum::<f32>() / samples.len() as f32;
    if energy < 0.00001 {
        return Err(Error::Audio("enrollment_too_quiet"));
    }
    Ok(samples)
}

pub fn run(
    input_id: &str,
    stop: Arc<AtomicBool>,
    mut personal: Option<Box<dyn PersonalVoice>>,
    mut noise: Box<dyn crate::modules::audio::application::NoiseReducer>,
    progress: &dyn Fn(&str) -> Result<()>,
) -> Result<String> {
    if cancelled(&stop) {
        return Ok("cancelled".into());
    }
    let host = cpal::default_host();
    let output = host
        .devices()
        .map_err(|_| audio_error())?
        .find(|d| d.description().is_ok_and(|x| x.name() == "BlackHole 2ch") && d.supports_output())
        .ok_or(Error::Audio("blackhole_2ch_not_installed"))?;
    let output_config = config(&output, false)?;
    let channels = usize::from(output_config.channels);
    let (mut output_frames, mut consumer) = rtrb::RingBuffer::<PcmFrame>::new(32);
    let fault = Arc::new(AtomicBool::new(false));
    let error_fault = fault.clone();
    let output_stop = stop.clone();
    let callback_fault = fault.clone();
    let mut frame = [0.0; FRAME];
    let mut position = FRAME;
    let stream = output
        .build_output_stream(
            output_config,
            move |out: &mut [f32], _| {
                if output_stop.load(Ordering::Acquire) || callback_fault.load(Ordering::Relaxed) {
                    out.fill(0.0);
                    return;
                }
                for samples in out.chunks_exact_mut(channels) {
                    if position == FRAME {
                        frame = consumer.pop().unwrap_or([0.0; FRAME]);
                        position = 0;
                    }
                    samples.fill(frame[position]);
                    position += 1;
                }
            },
            move |_| {
                error_fault.store(true, Ordering::Release);
            },
            None,
        )
        .map_err(|_| audio_error())?;
    stream.play().map_err(|_| audio_error())?;
    let mut capture = Capture::open(input_id, stop.clone())?;
    progress("audio_active")?;
    let mut downsample = Downsample::default();
    let mut input16 = Vec::with_capacity(2560);
    let mut pending = Vec::with_capacity(16);
    let result = (|| {
        while let Some(input) = capture.next(&stop)? {
            if fault.load(Ordering::Acquire) {
                return Err(Error::Audio("blackhole_output_failed"));
            }
            let mut filtered = [0.0; FRAME];
            noise.process(&input, &mut filtered);
            if let Some(voice) = personal.as_mut() {
                downsample.process(&input, &mut input16);
                pending.push(filtered);
                if input16.len() < 2560 {
                    continue;
                }
                let probability = voice.probability(&input16)?;
                if cancelled(&stop) {
                    break;
                }
                for mut frame in pending.drain(..) {
                    if probability < 0.7 {
                        frame.fill(0.0);
                    }
                    output_frames
                        .push(frame)
                        .map_err(|_| Error::Audio("audio_output_backpressure"))?;
                }
                input16.clear();
            } else {
                output_frames
                    .push(filtered)
                    .map_err(|_| Error::Audio("audio_output_backpressure"))?;
            }
        }
        Ok("audio_stopped".into())
    })();
    // Silence immediately on an error, including slow inference and overflow.
    stop.store(true, Ordering::Release);
    drop(capture);
    drop(stream);
    result
}
