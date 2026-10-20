use super::codec::{decode, encode};
use crate::commons::{Error, Result};
use crate::modules::operations::{
    application::event_name,
    domain::{Event, Operation, Status},
};
use rusqlite::{OptionalExtension, Transaction, params};

pub(super) fn get(tx: &Transaction<'_>, id: &str) -> Result<Operation> {
    let value = tx
        .query_row("SELECT document FROM operations WHERE id=?1", [id], |r| {
            r.get(0)
        })
        .optional()?;
    decode(value.ok_or(Error::NotFound)?)
}
pub(super) fn save(tx: &Transaction<'_>, operation: &Operation) -> Result<()> {
    tx.execute(
        "UPDATE operations SET document=?1 WHERE id=?2",
        params![encode(operation)?, operation.operation_id],
    )?;
    let time: String = tx.query_row("SELECT strftime('%Y-%m-%dT%H:%M:%fZ','now')", [], |r| {
        r.get(0)
    })?;
    let mut event = Event {
        event_id: 0,
        event_type: if operation.status == Status::Running && operation.detail.is_some() {
            "operation.progress".into()
        } else {
            event_name(operation.status).into()
        },
        schema_version: 1,
        module: "operations".into(),
        operation_id: operation.operation_id.clone(),
        occurred_at_utc: time,
        operation: operation.clone(),
    };
    tx.execute("INSERT INTO operation_events(document) VALUES ('')", [])?;
    event.event_id = tx.last_insert_rowid();
    tx.execute(
        "UPDATE operation_events SET document=?1 WHERE id=?2",
        params![encode(&event)?, event.event_id],
    )?;
    Ok(())
}
