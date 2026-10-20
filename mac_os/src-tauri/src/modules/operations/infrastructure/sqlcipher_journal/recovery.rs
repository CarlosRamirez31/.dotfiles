use crate::commons::Result;
use crate::modules::operations::{
    application::event_name,
    domain::{OperationKind, Status},
};
use rusqlite::{Transaction, params};

const SERVICE_RESTARTED: &str = "service_restarted";

pub(super) fn recover(tx: &Transaction<'_>) -> Result<()> {
    // Fixed-size SQL batch; preserve atomic recovery without per-operation queries.
    tx.execute_batch(
        "CREATE TEMP TABLE IF NOT EXISTS operations_recovery(id TEXT PRIMARY KEY);
         DELETE FROM operations_recovery;",
    )?;
    tx.execute(
        "INSERT INTO operations_recovery
         SELECT id FROM operations
         WHERE json_extract(document,'$.status') IN (?1,?2)
            OR (json_extract(document,'$.status')=?3
                AND json_extract(document,'$.kind') != ?4)",
        params![
            Status::Running.as_str(),
            Status::CancellationRequested.as_str(),
            Status::Accepted.as_str(),
            OperationKind::StorageCheck.as_str(),
        ],
    )?;
    tx.execute(
        "UPDATE operations
         SET document=json_set(document,
             '$.status',CASE WHEN json_extract(document,'$.status')=?1 THEN ?2 ELSE ?3 END,
             '$.detail',?4)
         WHERE id IN (SELECT id FROM operations_recovery)",
        params![
            Status::CancellationRequested.as_str(),
            Status::Cancelled.as_str(),
            Status::Interrupted.as_str(),
            SERVICE_RESTARTED,
        ],
    )?;
    tx.execute(
        "INSERT INTO operation_events(document)
         SELECT json_object(
             'eventId',0,
             'eventType',CASE WHEN json_extract(document,'$.status')=?1 THEN ?2 ELSE ?3 END,
             'schemaVersion',1,'module','operations','operationId',id,
             'occurredAtUtc',strftime('%Y-%m-%dT%H:%M:%fZ','now'),
             'operation',json(document))
         FROM operations WHERE id IN (SELECT id FROM operations_recovery) ORDER BY rowid",
        params![
            Status::Cancelled.as_str(),
            event_name(Status::Cancelled),
            event_name(Status::Interrupted),
        ],
    )?;
    tx.execute("DELETE FROM operations_recovery", [])?;
    Ok(())
}
