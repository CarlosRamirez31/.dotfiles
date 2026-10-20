use super::VoiceProfiles;
use crate::commons::utils::blocking;
use crate::commons::{Error, Result};
use crate::modules::personal_voice::domain::VoiceProfile;
use std::sync::Arc;

pub struct VoiceProfileService {
    profiles: Arc<dyn VoiceProfiles>,
}
impl VoiceProfileService {
    pub fn new(profiles: Arc<dyn VoiceProfiles>) -> Self {
        Self { profiles }
    }
    pub async fn list(&self) -> Result<Vec<VoiceProfile>> {
        let profiles = self.profiles.clone();
        blocking(move || profiles.list()).await
    }
    pub async fn delete(&self, id: String) -> Result<()> {
        validate_id(&id)?;
        let profiles = self.profiles.clone();
        blocking(move || profiles.delete(&id)).await
    }
    pub async fn set_default(&self, id: String) -> Result<()> {
        validate_id(&id)?;
        let profiles = self.profiles.clone();
        blocking(move || profiles.set_default(&id)).await
    }
}
fn validate_id(id: &str) -> Result<()> {
    uuid::Uuid::parse_str(id).map_err(|_| Error::Invalid)?;
    Ok(())
}
