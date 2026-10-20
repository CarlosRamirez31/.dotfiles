use crate::commons::{Error, utils::blocking};
use axum::Json;

pub(super) async fn audio_devices()
-> Result<Json<crate::modules::audio::infrastructure::Devices>, Error> {
    Ok(Json(
        blocking(crate::modules::audio::infrastructure::devices).await?,
    ))
}
