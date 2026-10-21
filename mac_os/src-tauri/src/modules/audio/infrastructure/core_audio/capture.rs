use super::{VIRTUAL_DEVICE_PREFIX, config::config};
use crate::commons::{AudioErrorCode, Error, Result};
use crate::modules::audio::application::{FRAME, PcmFrame, audio_error, cancelled};
use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use std::{
    sync::{
        Arc,
        atomic::{AtomicBool, Ordering},
    },
    time::{Duration, Instant},
};
pub(super) struct Capture {
    _stream: cpal::Stream,
    frames: rtrb::Consumer<PcmFrame>,
    fault: Arc<AtomicBool>,
}
impl Capture {
    pub(super) fn open(id: &str, stop: Arc<AtomicBool>) -> Result<Self> {
        let device = cpal::default_host()
            .device_by_id(&id.parse().map_err(|_| audio_error())?)
            .ok_or_else(audio_error)?;
        if device
            .description()
            .map_err(|_| audio_error())?
            .name()
            .contains(VIRTUAL_DEVICE_PREFIX)
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
    pub(super) fn next(&mut self, stop: &Arc<AtomicBool>) -> Result<Option<PcmFrame>> {
        next_frame(&mut self.frames, &self.fault, stop)
    }
}

fn next_frame(
    frames: &mut rtrb::Consumer<PcmFrame>,
    fault: &AtomicBool,
    stop: &Arc<AtomicBool>,
) -> Result<Option<PcmFrame>> {
    let deadline = Instant::now() + Duration::from_secs(3);
    loop {
        if cancelled(stop) {
            return Ok(None);
        }
        if fault.load(Ordering::Acquire) {
            return Err(Error::Audio(AudioErrorCode::AudioOverrunOrDeviceLost));
        }
        if let Ok(frame) = frames.pop() {
            return Ok(Some(frame));
        }
        if Instant::now() > deadline {
            return Err(Error::Audio(
                AudioErrorCode::MicrophoneTimeoutOrPermissionDenied,
            ));
        }
        std::thread::sleep(Duration::from_millis(2));
    }
}

#[cfg(test)]
#[path = "../../test/capture_fault.rs"]
mod test;
