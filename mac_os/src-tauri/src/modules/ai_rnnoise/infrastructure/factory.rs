use super::RnNoise;
use crate::modules::audio::application::{NoiseReducer, NoiseReducerFactory};
pub struct RnNoiseFactory;
impl NoiseReducerFactory for RnNoiseFactory {
    fn create(&self) -> Box<dyn NoiseReducer> {
        Box::new(RnNoise::default())
    }
}
