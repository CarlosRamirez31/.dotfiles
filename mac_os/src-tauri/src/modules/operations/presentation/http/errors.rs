use crate::commons::Error;
use axum::{
    Json,
    http::StatusCode,
    response::{IntoResponse, Response},
};

impl IntoResponse for Error {
    fn into_response(self) -> Response {
        let (status, code) = match self {
            Self::NotFound => (StatusCode::NOT_FOUND, "not_found"),
            Self::Conflict => (StatusCode::CONFLICT, "idempotency_conflict"),
            Self::Busy => (StatusCode::CONFLICT, "audio_session_active"),
            Self::Invalid => (StatusCode::BAD_REQUEST, "invalid_request"),
            Self::Capacity => (
                StatusCode::SERVICE_UNAVAILABLE,
                "operation_capacity_reached",
            ),
            Self::Storage => (StatusCode::INTERNAL_SERVER_ERROR, "storage_unavailable"),
            Self::Audio(code) => (StatusCode::CONFLICT, code.as_str()),
        };
        (status, Json(serde_json::json!({"error":code}))).into_response()
    }
}
