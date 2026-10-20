#[test]
fn rnnoise_executes_embedded_network_and_preserves_normalized_pcm() {
    use crate::modules::audio::application::NoiseReducer;
    let mut processor = crate::modules::ai_rnnoise::infrastructure::RnNoise::default();
    let mut output = [0.0; 480];
    let mut seed = 7_u32;
    for _ in 0..100 {
        let input = std::array::from_fn(|_| {
            seed = seed.wrapping_mul(1664525).wrapping_add(1013904223);
            ((seed >> 8) as f32 / 16777216.0 - 0.5) * 0.1
        });
        processor.process(&input, &mut output).unwrap();
        assert!(output.iter().all(|x| x.is_finite() && x.abs() <= 1.0));
    }
    assert!(output.iter().any(|x| x.abs() > 0.0));
}

#[test]
fn rnnoise_rejects_nonfinite_pcm_as_typed_error() {
    use crate::modules::audio::{application::NoiseReducer, domain::capability::CapabilityError};
    let mut processor = crate::modules::ai_rnnoise::infrastructure::RnNoise::default();
    assert_eq!(
        processor.process(&[f32::NAN; 480], &mut [0.0; 480]),
        Err(CapabilityError::InvalidInput)
    );
}
