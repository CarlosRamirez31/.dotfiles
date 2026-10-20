use crate::modules::audio::{
    application::{AudioPipeline, NoiseReducer, PersonalVoice},
    domain::{FRAME, PcmFrame, capability::CapabilityResult},
};
use std::sync::{
    Arc,
    atomic::{AtomicBool, Ordering},
};

struct Noise;
impl NoiseReducer for Noise {
    fn process(&mut self, input: &PcmFrame, output: &mut PcmFrame) -> CapabilityResult<()> {
        output.copy_from_slice(input);
        Ok(())
    }
}
struct Voice {
    probability: f32,
    cancel: Option<Arc<AtomicBool>>,
}
impl PersonalVoice for Voice {
    fn probability(&mut self, pcm: &[f32]) -> CapabilityResult<f32> {
        assert_eq!(pcm.len(), 2560);
        if let Some(stop) = &self.cancel {
            stop.store(true, Ordering::Release);
        }
        Ok(self.probability)
    }
}

#[test]
fn pipeline_buffers_complete_voice_window_and_applies_threshold() {
    for probability in [0.2, 0.9] {
        let mut pipeline = AudioPipeline::new(
            Some(Box::new(Voice {
                probability,
                cancel: None,
            })),
            Box::new(Noise),
            0.7,
        );
        let stop = Arc::new(AtomicBool::new(false));
        let mut output = Vec::new();
        for _ in 0..15 {
            pipeline
                .process(&[0.25; FRAME], &stop, &mut |frame| {
                    output.push(frame);
                    Ok(())
                })
                .unwrap();
        }
        assert!(output.is_empty());
        pipeline
            .process(&[0.25; FRAME], &stop, &mut |frame| {
                output.push(frame);
                Ok(())
            })
            .unwrap();
        assert_eq!(output.len(), 16);
        let expected = if probability < 0.7 { 0.0 } else { 0.25 };
        assert!(output.iter().flatten().all(|sample| *sample == expected));
    }
}

#[test]
fn pipeline_does_not_emit_pending_audio_after_inference_cancels() {
    let stop = Arc::new(AtomicBool::new(false));
    let mut pipeline = AudioPipeline::new(
        Some(Box::new(Voice {
            probability: 1.0,
            cancel: Some(stop.clone()),
        })),
        Box::new(Noise),
        0.7,
    );
    for _ in 0..16 {
        pipeline
            .process(&[0.25; FRAME], &stop, &mut |_| {
                panic!("cancelled_audio_emitted")
            })
            .unwrap();
    }
    assert!(stop.load(Ordering::Acquire));
}

#[test]
fn noise_only_pipeline_emits_each_frame_without_voice_buffering() {
    let mut pipeline = AudioPipeline::new(None, Box::new(Noise), 0.7);
    let stop = Arc::new(AtomicBool::new(false));
    let mut output = Vec::new();
    pipeline
        .process(&[0.25; FRAME], &stop, &mut |frame| {
            output.push(frame);
            Ok(())
        })
        .unwrap();
    assert_eq!(output, vec![[0.25; FRAME]]);
}
