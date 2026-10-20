mod audio_controller;
mod errors;
mod events_controller;
mod operations_controller;
mod security;
mod voice_profiles_controller;

use crate::modules::operations::application::Operations;
use audio_controller::*;
use axum::{
    Router, middleware,
    routing::{delete, get, post},
};
use events_controller::*;
use operations_controller::*;
use security::protect;
use voice_profiles_controller::*;

#[derive(Clone)]
pub struct Bff {
    pub operations: Operations,
    pub token: String,
    pub api_version: String,
    pub voices: std::sync::Arc<dyn crate::modules::personal_voice::application::VoiceProfiles>,
}

pub fn router(state: Bff) -> Router {
    let prefix = format!("/{}", state.api_version);
    let routes = Router::new()
        .route("/operations/storage-check", post(accept))
        .route("/operations", get(recent))
        .route("/commands", post(command))
        .route("/operations/{id}", get(operation))
        .route("/operations/{id}/cancel", post(cancel))
        .route("/events", get(events))
        .route("/audio/devices", get(audio_devices))
        .route("/voice-profiles", get(voice_profiles))
        .route("/voice-profiles/{id}", delete(delete_voice_profile))
        .route("/voice-profiles/{id}/default", post(default_voice_profile));
    Router::new()
        .nest(&prefix, routes)
        .layer(middleware::from_fn_with_state(state.clone(), protect))
        .with_state(state)
}

const SNAPSHOT_CURSOR_HEADER: &str = "X-Event-Cursor";
