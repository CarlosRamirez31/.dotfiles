use crate::commons::Error;
use crate::modules::operations::{
    application::{Operations, blocking},
    domain::Operation,
};
use axum::{
    Json, Router,
    extract::{Path, Request, State},
    http::{HeaderMap, StatusCode, header},
    middleware::{self, Next},
    response::{
        IntoResponse, Response,
        sse::{Event as SseEvent, KeepAlive, Sse},
    },
    routing::{get, post},
};
use std::{convert::Infallible, time::Duration};

#[derive(Clone)]
pub struct Bff {
    pub operations: Operations,
    pub token: String,
}

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
            Self::Audio(code) => (StatusCode::CONFLICT, code),
        };
        (status, Json(serde_json::json!({"error":code}))).into_response()
    }
}

pub fn router(state: Bff) -> Router {
    Router::new()
        .route("/v1/operations/storage-check", post(accept))
        .route("/v1/operations", get(recent))
        .route("/v1/commands", post(command))
        .route("/v1/operations/{id}", get(operation))
        .route("/v1/operations/{id}/cancel", post(cancel))
        .route("/v1/events", get(events))
        .route("/v1/audio/devices", get(audio_devices))
        .layer(middleware::from_fn_with_state(state.clone(), protect))
        .with_state(state)
}
async fn protect(State(state): State<Bff>, request: Request, next: Next) -> Response {
    let started = std::time::Instant::now();
    let route = request
        .extensions()
        .get::<axum::extract::MatchedPath>()
        .map(|path| path.as_str().to_owned())
        .unwrap_or_else(|| "unmatched".into());
    let origin = request.headers().get(header::ORIGIN).cloned();
    if let Some(origin) = &origin {
        let allowed = origin == "tauri://localhost"
            || origin == "http://tauri.localhost"
            || (cfg!(debug_assertions) && origin == "http://localhost:1420");
        if !allowed {
            return StatusCode::FORBIDDEN.into_response();
        }
    }
    let mut response = if request.method() == axum::http::Method::OPTIONS {
        StatusCode::NO_CONTENT.into_response()
    } else {
        let expected = format!("Bearer {}", state.token);
        if request
            .headers()
            .get(header::AUTHORIZATION)
            .and_then(|h| h.to_str().ok())
            != Some(expected.as_str())
        {
            return StatusCode::UNAUTHORIZED.into_response();
        }
        next.run(request).await
    };
    tracing::info!(
        event = "http.response",
        route,
        status = response.status().as_u16(),
        elapsed_ms = started.elapsed().as_millis() as u64
    );
    let headers = response.headers_mut();
    headers.insert(header::CACHE_CONTROL, "no-store".parse().unwrap());
    headers.insert(header::X_CONTENT_TYPE_OPTIONS, "nosniff".parse().unwrap());
    if let Some(origin) = origin {
        headers.insert(header::ACCESS_CONTROL_ALLOW_ORIGIN, origin);
        headers.insert(header::VARY, "Origin".parse().unwrap());
        headers.insert(
            header::ACCESS_CONTROL_ALLOW_METHODS,
            "GET, POST, OPTIONS".parse().unwrap(),
        );
        headers.insert(
            header::ACCESS_CONTROL_ALLOW_HEADERS,
            "Authorization, Idempotency-Key, Last-Event-ID, Content-Type"
                .parse()
                .unwrap(),
        );
        headers.insert(
            header::ACCESS_CONTROL_EXPOSE_HEADERS,
            "Location".parse().unwrap(),
        );
    }
    response
}
async fn accept(
    State(bff): State<Bff>,
    headers: HeaderMap,
    body: axum::body::Bytes,
) -> Result<Response, Error> {
    // This command has no parameters. Reject payloads rather than silently ignoring them.
    if !body.is_empty() {
        return Err(Error::Invalid);
    }
    let key = headers
        .get("Idempotency-Key")
        .and_then(|h| h.to_str().ok())
        .ok_or(Error::Invalid)?
        .to_owned();
    let operation = bff
        .operations
        .accept(key, crate::commons::Command::CheckStorage)
        .await?;
    Ok((
        StatusCode::ACCEPTED,
        [(
            header::LOCATION,
            format!("/v1/operations/{}", operation.operation_id),
        )],
        Json(operation),
    )
        .into_response())
}
async fn recent(State(bff): State<Bff>) -> Result<Json<Vec<Operation>>, Error> {
    Ok(Json(
        blocking(move || bff.operations.journal.recent()).await?,
    ))
}
async fn operation(
    State(bff): State<Bff>,
    Path(id): Path<String>,
) -> Result<Json<Operation>, Error> {
    Ok(Json(
        blocking(move || bff.operations.journal.get(&id)).await?,
    ))
}
async fn cancel(State(bff): State<Bff>, Path(id): Path<String>) -> Result<Json<Operation>, Error> {
    Ok(Json(bff.operations.cancel(id).await?))
}
async fn events(State(bff): State<Bff>, headers: HeaderMap) -> Result<Response, Error> {
    let mut cursor = match headers.get("Last-Event-ID") {
        Some(value) => value
            .to_str()
            .ok()
            .and_then(|s| s.parse::<i64>().ok())
            .filter(|n| *n >= 0)
            .ok_or(Error::Invalid)?,
        None => 0,
    };
    let journal = bff.operations.journal.clone();
    let last = blocking(move || journal.last_event_id()).await?;
    if cursor > last {
        return Err(Error::Invalid);
    }
    let stream = async_stream::stream! {
        loop {
            // The journal is the replay source; the timeout also covers a notification race.
            let changed = bff.operations.changed.notified();
            let journal = bff.operations.journal.clone();
            let batch = match blocking(move || journal.events(cursor)).await {
                Ok(batch) => batch, Err(_) => break,
            };
            if batch.is_empty() {
                tokio::select! { _ = changed => {}, _ = tokio::time::sleep(Duration::from_secs(1)) => {} }
                continue;
            }
            for event in batch {
                cursor = event.event_id;
                let Ok(data) = serde_json::to_string(&event) else { return; };
                yield Ok::<_, Infallible>(SseEvent::default().id(cursor.to_string()).event(&event.event_type).data(data));
            }
        }
    };
    Ok(Sse::new(stream)
        .keep_alive(KeepAlive::new().interval(Duration::from_secs(15)))
        .into_response())
}

async fn command(
    State(bff): State<Bff>,
    headers: HeaderMap,
    Json(command): Json<crate::commons::Command>,
) -> Result<Response, Error> {
    let key = headers
        .get("Idempotency-Key")
        .and_then(|h| h.to_str().ok())
        .ok_or(Error::Invalid)?
        .to_owned();
    let operation = bff.operations.accept(key, command).await?;
    Ok((
        StatusCode::ACCEPTED,
        [(
            header::LOCATION,
            format!("/v1/operations/{}", operation.operation_id),
        )],
        Json(operation),
    )
        .into_response())
}

async fn audio_devices() -> Result<Json<crate::modules::audio::infrastructure::Devices>, Error> {
    Ok(Json(
        blocking(crate::modules::audio::infrastructure::devices).await?,
    ))
}
