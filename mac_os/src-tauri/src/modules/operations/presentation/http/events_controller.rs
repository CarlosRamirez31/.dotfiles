use super::Bff;
use crate::commons::Error;
use axum::{
    extract::State,
    http::HeaderMap,
    response::{
        IntoResponse, Response,
        sse::{Event as SseEvent, KeepAlive, Sse},
    },
};
use std::{convert::Infallible, time::Duration};

pub(super) async fn events(State(bff): State<Bff>, headers: HeaderMap) -> Result<Response, Error> {
    let mut cursor = match headers.get("Last-Event-ID") {
        Some(value) => value
            .to_str()
            .ok()
            .and_then(|s| s.parse::<i64>().ok())
            .filter(|n| *n >= 0)
            .ok_or(Error::Invalid)?,
        None => 0,
    };
    bff.operations.validate_cursor(cursor).await?;
    let stream = async_stream::stream! {
        loop {
            // The journal is the replay source; the timeout also covers a notification race.
            let changed = bff.operations.changed.notified();
            let batch = match bff.operations.events_after(cursor).await {
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
