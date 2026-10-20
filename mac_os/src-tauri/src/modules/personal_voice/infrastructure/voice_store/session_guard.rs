use crate::commons::{Error, Result};
use crate::modules::operations::domain::{OperationKind, Status};
use rusqlite::{Connection, params};
pub(super) fn idle(connection: &Connection) -> Result<()> {
    let active: i64 = connection.query_row("SELECT count(*) FROM operations WHERE json_extract(document,'$.kind') != ?1 AND json_extract(document,'$.status') IN (?2,?3,?4)", params![OperationKind::StorageCheck.as_str(),Status::Accepted.as_str(),Status::Running.as_str(),Status::CancellationRequested.as_str()], |r| r.get(0))?;
    if active != 0 {
        return Err(Error::Busy);
    }
    Ok(())
}
