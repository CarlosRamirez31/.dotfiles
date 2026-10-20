use super::codec::decode;
use crate::{commons::Result, modules::operations::domain::Event};
use rusqlite::Connection;

pub(super) fn copy_business_events(connection: &Connection, after: i64) -> Result<()> {
    let mut query =
        connection.prepare("SELECT id,document FROM operation_events WHERE id>?1 ORDER BY id")?;
    let rows = query.query_map([after], |row| {
        Ok((row.get::<_, i64>(0)?, row.get::<_, String>(1)?))
    })?;
    for row in rows {
        let (id, document) = row?;
        let event: Event = decode(document)?;
        // Allowlist: never serialize the command, input device, embedding or arbitrary detail.
        tracing::info!(target:"business", event_id=id, event_type=%event.event_type,
          schema_version=event.schema_version, module=%event.module, operation_id=%event.operation_id,
          occurred_at_utc=%event.occurred_at_utc, status=?event.operation.status);
    }
    Ok(())
}
