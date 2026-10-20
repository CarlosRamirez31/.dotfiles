#[test]
fn downsample_preserves_block_continuity_and_suppresses_aliasing() {
    use crate::modules::audio::infrastructure::Downsample;
    let signal: Vec<f32> = (0..4800)
        .map(|i| (2.0 * std::f32::consts::PI * 12000.0 * i as f32 / 48000.0).sin())
        .collect();
    let mut whole = Vec::new();
    Downsample::default().process(&signal, &mut whole);
    let mut split = Vec::new();
    let mut converter = Downsample::default();
    for chunk in signal.chunks(77) {
        converter.process(chunk, &mut split);
    }
    assert_eq!(split, whole);
    assert_eq!(whole.len(), 1600);
    let rms = (whole[100..].iter().map(|x| x * x).sum::<f32>() / 1500.0).sqrt();
    assert!(rms < 0.01, "Aliased 12 kHz energy: {rms}");
}
