use super::select_config;
use crate::commons::{AudioErrorCode, Error};
use cpal::{SampleFormat, SupportedBufferSize, SupportedStreamConfigRange};

fn range(channels: u16, min: u32, max: u32, format: SampleFormat) -> SupportedStreamConfigRange {
    SupportedStreamConfigRange::new(channels, min, max, SupportedBufferSize::Unknown, format)
}

#[test]
fn incompatible_formats_are_rejected_before_opening_a_stream() {
    for candidate in [
        range(1, 44100, 44100, SampleFormat::F32),
        range(1, 48000, 48000, SampleFormat::I16),
        range(6, 48000, 48000, SampleFormat::F32),
        range(0, 48000, 48000, SampleFormat::F32),
    ] {
        assert!(matches!(
            select_config([candidate]),
            Err(Error::Audio(
                AudioErrorCode::RequiresFloat3248khzMonoOrStereo
            ))
        ));
    }
    assert!(select_config([]).is_err());
}

#[test]
fn negotiation_selects_supported_mono_at_48khz_without_changing_device() {
    let config = select_config([
        range(2, 44100, 96000, SampleFormat::F32),
        range(1, 44100, 96000, SampleFormat::F32),
    ])
    .unwrap();
    assert_eq!(config.channels, 1);
    assert_eq!(config.sample_rate, 48000);
    assert_eq!(
        select_config([range(2, 48000, 48000, SampleFormat::F32)])
            .unwrap()
            .channels,
        2
    );
}
