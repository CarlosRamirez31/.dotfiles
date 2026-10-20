use super::Bff;
use crate::{commons::Error, modules::personal_voice::application::VoiceProfileService};
use axum::{
    Json,
    extract::{Path, State},
    http::StatusCode,
};

pub(super) async fn voice_profiles(
    State(bff): State<Bff>,
) -> Result<Json<Vec<crate::modules::personal_voice::domain::VoiceProfile>>, Error> {
    Ok(Json(VoiceProfileService::new(bff.voices).list().await?))
}
pub(super) async fn delete_voice_profile(
    State(bff): State<Bff>,
    Path(id): Path<String>,
) -> Result<StatusCode, Error> {
    VoiceProfileService::new(bff.voices).delete(id).await?;
    Ok(StatusCode::NO_CONTENT)
}
pub(super) async fn default_voice_profile(
    State(bff): State<Bff>,
    Path(id): Path<String>,
) -> Result<StatusCode, Error> {
    VoiceProfileService::new(bff.voices).set_default(id).await?;
    Ok(StatusCode::NO_CONTENT)
}
