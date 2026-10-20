use super::Bff;
use crate::commons::protocol;
use axum::{
    extract::{Request, State},
    http::{StatusCode, header},
    middleware::Next,
    response::{IntoResponse, Response},
};

pub(super) async fn protect(State(state): State<Bff>, request: Request, next: Next) -> Response {
    let started = std::time::Instant::now();
    let route = request
        .extensions()
        .get::<axum::extract::MatchedPath>()
        .map(|path| path.as_str().to_owned())
        .unwrap_or_else(|| "unmatched".into());
    let origin = request.headers().get(header::ORIGIN).cloned();
    if let Some(origin) = &origin {
        let allowed = origin == protocol::TAURI_ORIGIN
            || origin == protocol::TAURI_HTTP_ORIGIN
            || (cfg!(debug_assertions) && origin == protocol::DEVELOPMENT_ORIGIN);
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
            "GET, POST, DELETE, OPTIONS".parse().unwrap(),
        );
        headers.insert(
            header::ACCESS_CONTROL_ALLOW_HEADERS,
            "Authorization, Idempotency-Key, Last-Event-ID, Content-Type, X-Event-Cursor"
                .parse()
                .unwrap(),
        );
        headers.insert(
            header::ACCESS_CONTROL_EXPOSE_HEADERS,
            "Location, X-Event-Cursor".parse().unwrap(),
        );
    }
    response
}
