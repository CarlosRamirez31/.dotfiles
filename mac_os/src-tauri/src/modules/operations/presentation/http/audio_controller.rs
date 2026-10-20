use super::Bff;
use crate::{commons::Error, modules::audio::domain::Devices};
use axum::{Json, extract::State};

pub(super) async fn audio_devices(State(bff): State<Bff>) -> Result<Json<Devices>, Error> {
    Ok(Json(bff.devices.list().await?))
}
