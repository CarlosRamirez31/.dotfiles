use super::{VIRTUAL_DEVICE_NAME, config::config};
use crate::commons::{AudioErrorCode, Error, Result};
use crate::modules::audio::application::{FRAME, PcmFrame, audio_error};
use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use std::sync::{
    Arc,
    atomic::{AtomicBool, Ordering},
};
pub(super) struct Output {
    _stream: cpal::Stream,
    frames: rtrb::Producer<PcmFrame>,
    fault: Arc<AtomicBool>,
}
impl Output {
    pub(super) fn open(stop: Arc<AtomicBool>) -> Result<Self> {
        let host = cpal::default_host();
        let output = host
            .devices()
            .map_err(|_| audio_error())?
            .find(|d| {
                d.description()
                    .is_ok_and(|x| x.name() == VIRTUAL_DEVICE_NAME)
                    && d.supports_output()
            })
            .ok_or(Error::Audio(AudioErrorCode::Blackhole2chNotInstalled))?;
        let output_config = config(&output, false)?;
        let channels = usize::from(output_config.channels);
        let (output_frames, mut consumer) = rtrb::RingBuffer::<PcmFrame>::new(32);
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
                    if output_stop.load(Ordering::Acquire) || callback_fault.load(Ordering::Relaxed)
                    {
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
        Ok(Self {
            _stream: stream,
            frames: output_frames,
            fault,
        })
    }
    pub(super) fn check(&self) -> Result<()> {
        check_fault(&self.fault)
    }
    pub(super) fn push(&mut self, frame: PcmFrame) -> Result<()> {
        push_frame(&mut self.frames, frame)
    }
}

fn check_fault(fault: &AtomicBool) -> Result<()> {
    if fault.load(Ordering::Acquire) {
        return Err(Error::Audio(AudioErrorCode::BlackholeOutputFailed));
    }
    Ok(())
}
fn push_frame(frames: &mut rtrb::Producer<PcmFrame>, frame: PcmFrame) -> Result<()> {
    frames
        .push(frame)
        .map_err(|_| Error::Audio(AudioErrorCode::AudioOutputBackpressure))
}

#[cfg(test)]
#[path = "../../test/output_fault.rs"]
mod test;
