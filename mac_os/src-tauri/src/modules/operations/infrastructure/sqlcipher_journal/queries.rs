use super::{codec::decode, records};
use crate::{
    commons::Result,
    modules::operations::domain::{Event, Operation},
};
use rusqlite::{Transaction, params};

pub(super) fn get(tx: &Transaction<'_>, id: &str) -> Result<Operation> {
    records::get(tx, id)
}

pub(super) fn recent(tx: &Transaction<'_>) -> Result<Vec<Operation>> {
    let mut query = tx.prepare("SELECT document FROM operations ORDER BY rowid DESC LIMIT 100")?;
    query
        .query_map([], |r| r.get::<_, String>(0))?
        .map(|row| decode(row?))
        .collect()
}

pub(super) fn snapshot(tx: &Transaction<'_>) -> Result<(Vec<Operation>, i64)> {
    let cursor = tx.query_row(
        "SELECT coalesce(max(id),0) FROM operation_events",
        [],
        |r| r.get(0),
    )?;
    let mut query = tx.prepare("SELECT document FROM operations ORDER BY rowid DESC LIMIT 100")?;
    let items = query
        .query_map([], |r| r.get::<_, String>(0))?
        .map(|row| decode(row?))
        .collect::<Result<Vec<Operation>>>()?;
    Ok((items, cursor))
}

pub(super) fn events(tx: &Transaction<'_>, after: i64, event_batch: i64) -> Result<Vec<Event>> {
    let mut query =
        tx.prepare("SELECT id,document FROM operation_events WHERE id>?1 ORDER BY id LIMIT ?2")?;
    query
        .query_map(params![after, event_batch], |r| {
            Ok((r.get::<_, i64>(0)?, r.get::<_, String>(1)?))
        })?
        .map(|row| {
            let (id, document) = row?;
            let mut event: Event = decode(document)?;
            event.event_id = id;
            Ok(event)
        })
        .collect()
}

pub(super) fn last_event_id(tx: &Transaction<'_>) -> Result<i64> {
    Ok(tx.query_row(
        "SELECT coalesce(max(id),0) FROM operation_events",
        [],
        |r| r.get(0),
    )?)
}
