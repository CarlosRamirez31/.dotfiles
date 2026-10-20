/// Native RNNoise adapter. Model weights are embedded by the pinned nnnoiseless crate.
pub struct RnNoise {
    state: Box<nnnoiseless::DenoiseState<'static>>,
}
impl Default for RnNoise {
    fn default() -> Self {
        Self {
            state: nnnoiseless::DenoiseState::new(),
        }
    }
}
impl crate::modules::audio::application::NoiseReducer for RnNoise {
    fn process(
        &mut self,
        input: &[f32; 480],
        output: &mut [f32; 480],
    ) -> crate::modules::audio::domain::capability::CapabilityResult<()> {
        use crate::modules::audio::domain::capability::CapabilityError;
        if input.iter().any(|v| !v.is_finite()) {
            return Err(CapabilityError::InvalidInput);
        }
        let scaled = input.map(|sample| sample.clamp(-1.0, 1.0) * 32768.0);
        self.state.process_frame(output, &scaled);
        if output.iter().any(|v| !v.is_finite()) {
            return Err(CapabilityError::InvalidResponse);
        }
        for sample in output {
            *sample = (*sample / 32768.0).clamp(-1.0, 1.0);
        }
        Ok(())
    }
}
