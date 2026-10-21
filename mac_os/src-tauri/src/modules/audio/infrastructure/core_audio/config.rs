use crate::commons::{AudioErrorCode, Error, Result};
use crate::modules::audio::application::audio_error;
use cpal::traits::DeviceTrait;
pub(super) fn config(device: &cpal::Device, input: bool) -> Result<cpal::StreamConfig> {
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
    select_config(ranges)
}

fn select_config(
    ranges: impl IntoIterator<Item = cpal::SupportedStreamConfigRange>,
) -> Result<cpal::StreamConfig> {
    let range = ranges
        .into_iter()
        .filter(|c| {
            c.sample_format() == cpal::SampleFormat::F32
                && c.min_sample_rate() <= 48000
                && c.max_sample_rate() >= 48000
                && (1..=2).contains(&c.channels())
        })
        .min_by_key(|c| c.channels())
        .ok_or(Error::Audio(
            AudioErrorCode::RequiresFloat3248khzMonoOrStereo,
        ))?;
    Ok(range.with_sample_rate(48000).config())
}

#[cfg(test)]
#[path = "../../test/config.rs"]
mod test;
