use serde::{Deserialize, Serialize};
#[derive(Clone, Serialize, Deserialize)]
pub struct VoiceOptions {
    pub load_seconds: u64,
    pub inference_seconds: u64,
    pub enroll_seconds: u64,
    pub threshold: f32,
    pub runtime: Option<std::path::PathBuf>,
}
impl Default for VoiceOptions {
    fn default() -> Self {
        Self {
            load_seconds: 120,
            inference_seconds: 2,
            enroll_seconds: 60,
            threshold: 0.7,
            runtime: None,
        }
    }
}
