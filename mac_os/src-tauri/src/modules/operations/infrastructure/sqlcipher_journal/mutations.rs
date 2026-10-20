use super::{
    codec::{decode, encode},
    records::{get, save},
};
use crate::commons::{Command, Error, Result};
use crate::modules::operations::{
    application::{Completion, lifecycle, options::OperationsOptions},
    domain::{Operation, OperationKind, Status},
};
use rusqlite::{OptionalExtension, Transaction, params};

pub(super) fn accept(
    tx: &Transaction<'_>,
    key: &str,
    command: Command,
    options: &OperationsOptions,
) -> Result<Operation> {
    let kind = command.kind();

    let old: Option<String> = tx
        .query_row(
            "SELECT document FROM operations WHERE idempotency_key=?1",
            [key],
            |r| r.get(0),
        )
        .optional()?;
    if let Some(old) = old {
        let operation: Operation = decode(old)?;
        return if operation.command == command {
            Ok(operation)
        } else {
            Err(Error::Conflict)
        };
    }
    if !matches!(command, Command::CheckStorage) {
        let active: i64 = tx.query_row("SELECT count(*) FROM operations WHERE json_extract(document,'$.kind') != ?1 AND json_extract(document,'$.status') IN (?2,?3,?4)", params![OperationKind::StorageCheck.as_str(),Status::Accepted.as_str(),Status::Running.as_str(),Status::CancellationRequested.as_str()], |r| r.get(0))?;
        if active > 0 {
            return Err(Error::Busy);
        }
    }
    let total: i64 = tx.query_row("SELECT count(*) FROM operations", [], |r| r.get(0))?;
    let pending: i64 = tx.query_row(
        "SELECT count(*) FROM operations WHERE json_extract(document,'$.status') IN (?1,?2,?3)",
        params![
            Status::Accepted.as_str(),
            Status::Running.as_str(),
            Status::CancellationRequested.as_str()
        ],
        |r| r.get(0),
    )?;
    if total >= options.max_operations || pending >= options.max_pending {
        return Err(Error::Capacity);
    }
    let operation = Operation {
        operation_id: uuid::Uuid::new_v4().to_string(),
        kind,
        command,
        status: Status::Accepted,
        detail: None,
    };
    tx.execute(
        "INSERT INTO operations VALUES (?1,?2,?3)",
        params![operation.operation_id, key, encode(&operation)?],
    )?;
    save(tx, &operation)?;
    Ok(operation)
}

pub(super) fn claim(tx: &Transaction<'_>) -> Result<Option<Operation>> {
    let document: Option<String> = tx.query_row("SELECT document FROM operations WHERE json_extract(document,'$.status')=?1 ORDER BY rowid LIMIT 1", [Status::Accepted.as_str()], |r| r.get(0)).optional()?;
    let Some(document) = document else {
        return Ok(None);
    };
    let mut operation: Operation = decode(document)?;
    operation.status = Status::Running;
    save(tx, &operation)?;
    Ok(Some(operation))
}

pub(super) fn finish(tx: &Transaction<'_>, id: &str, result: Result<Completion>) -> Result<()> {
    let mut operation = get(tx, id)?;
    if !lifecycle::complete(&mut operation, result) {
        return Ok(());
    }
    save(tx, &operation)
}

pub(super) fn cancel(tx: &Transaction<'_>, id: &str) -> Result<Operation> {
    let mut operation = get(tx, id)?;
    if !lifecycle::request_cancel(&mut operation) {
        return Ok(operation);
    }
    save(tx, &operation)?;
    Ok(operation)
}

pub(super) fn progress(tx: &Transaction<'_>, id: &str, detail: &str) -> Result<()> {
    let mut operation = get(tx, id)?;
    if operation.status == Status::Running {
        operation.detail = Some(detail.into());
        save(tx, &operation)?;
    }
    Ok(())
}
