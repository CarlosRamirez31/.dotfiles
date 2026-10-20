/// Stateful 63-tap low-pass before 48 -> 16 kHz decimation, outside the audio callback.
pub struct Downsample {
    history: [f32; 63],
    coefficients: [f32; 63],
    position: usize,
    phase: usize,
}
impl Default for Downsample {
    fn default() -> Self {
        let mut coefficients = [0.0; 63];
        for (i, coefficient) in coefficients.iter_mut().enumerate() {
            let x = i as f32 - 31.0;
            let sinc = if x == 0.0 {
                0.3
            } else {
                (std::f32::consts::PI * 0.3 * x).sin() / (std::f32::consts::PI * x)
            };
            *coefficient =
                sinc * (0.5 - 0.5 * (2.0 * std::f32::consts::PI * i as f32 / 62.0).cos());
        }
        let sum: f32 = coefficients.iter().sum();
        coefficients.iter_mut().for_each(|x| *x /= sum);
        Self {
            history: [0.0; 63],
            coefficients,
            position: 0,
            phase: 0,
        }
    }
}
impl Downsample {
    pub fn process(&mut self, input: &[f32], output: &mut Vec<f32>) {
        for sample in input {
            self.history[self.position] = *sample;
            self.position = (self.position + 1) % 63;
            self.phase = (self.phase + 1) % 3;
            if self.phase == 0 {
                output.push(
                    (0..63)
                        .map(|i| self.coefficients[i] * self.history[(self.position + 62 - i) % 63])
                        .sum(),
                );
            }
        }
    }
}
