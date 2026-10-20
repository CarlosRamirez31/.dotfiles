mod acl;
mod connection;
mod mutations;
mod queries;
mod session_guard;
use crate::commons::Result;
use crate::modules::personal_voice::{application::VoiceProfiles, domain::VoiceProfile};
use std::path::PathBuf;
pub struct VoiceStore {
    pub path: PathBuf,
    pub key: String,
    pub max_profiles: usize,
}
impl VoiceProfiles for VoiceStore {
    fn list(&self) -> Result<Vec<VoiceProfile>> {
        queries::list(self)
    }
    fn embedding(&self, id: &str) -> Result<Vec<f32>> {
        queries::embedding(self, id)
    }
    fn save_profile(&self, id: &str, name: &str, embedding: &[f32], replace: bool) -> Result<()> {
        mutations::save_profile(self, id, name, embedding, replace)
    }
    fn set_default(&self, id: &str) -> Result<()> {
        mutations::set_default(self, id)
    }
    fn delete(&self, id: &str) -> Result<()> {
        mutations::delete(self, id)
    }
    fn load(&self) -> Result<Vec<f32>> {
        queries::load(self)
    }
    fn save(&self, embedding: &[f32]) -> Result<()> {
        mutations::save(self, embedding)
    }
}
