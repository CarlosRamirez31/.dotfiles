use super::{Bff, SNAPSHOT_CURSOR_HEADER};
use crate::{commons::Error, modules::operations::domain::Operation};
use axum::{
    Json,
    extract::{Path, State},
    http::{HeaderMap, StatusCode, header},
    response::{IntoResponse, Response},
};

pub(super) async fn accept(
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
            format!("/{}/operations/{}", bff.api_version, operation.operation_id),
        )],
        Json(operation),
    )
        .into_response())
}
pub(super) async fn recent(State(bff): State<Bff>, headers: HeaderMap) -> Result<Response, Error> {
    if !headers.contains_key(SNAPSHOT_CURSOR_HEADER) {
        let items = bff.operations.recent().await?;
        return Ok(Json(items).into_response());
    }
    let (items, cursor) = bff.operations.snapshot().await?;
    Ok(([(SNAPSHOT_CURSOR_HEADER, cursor.to_string())], Json(items)).into_response())
}

pub(super) async fn operation(
    State(bff): State<Bff>,
    Path(id): Path<String>,
) -> Result<Json<Operation>, Error> {
    Ok(Json(bff.operations.get(id).await?))
}
pub(super) async fn cancel(
    State(bff): State<Bff>,
    Path(id): Path<String>,
) -> Result<Json<Operation>, Error> {
    Ok(Json(bff.operations.cancel(id).await?))
}
pub(super) async fn command(
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
            format!("/{}/operations/{}", bff.api_version, operation.operation_id),
        )],
        Json(operation),
    )
        .into_response())
}
