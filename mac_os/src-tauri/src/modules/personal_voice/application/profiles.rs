use super::super::domain::VoiceProfile;
use crate::commons::Result;
pub trait VoiceProfiles: Send + Sync {
    fn list(&self) -> Result<Vec<VoiceProfile>>;
    fn embedding(&self, id: &str) -> Result<Vec<f32>>;
    fn save_profile(&self, id: &str, name: &str, embedding: &[f32], replace: bool) -> Result<()>;
    fn set_default(&self, id: &str) -> Result<()>;
    fn delete(&self, id: &str) -> Result<()>;
    fn load(&self) -> Result<Vec<f32>>;
    fn save(&self, embedding: &[f32]) -> Result<()>;
}
