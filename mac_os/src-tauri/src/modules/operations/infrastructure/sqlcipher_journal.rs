use crate::commons::{Command, Error, Result};
use crate::modules::operations::{
    application::{Completion, Journal, event_name},
    domain::{Event, Operation, OperationKind, Status},
};
use rusqlite::{Connection, OptionalExtension, Transaction, params};
use std::{path::Path, sync::Mutex};

pub struct SqlCipherJournal {
    connection: Mutex<Connection>,
    options: crate::modules::operations::application::options::OperationsOptions,
}
impl SqlCipherJournal {
    #[cfg(test)]
    pub fn open(path: &Path, key: &str) -> Result<Self> {
        Self::configured(path, key, Default::default())
    }
    pub fn configured(
        path: &Path,
        key: &str,
        options: crate::modules::operations::application::options::OperationsOptions,
    ) -> Result<Self> {
        let connection = Connection::open(path)?;
        connection.pragma_update(None, "key", key)?;
        let cipher: String = connection.query_row("PRAGMA cipher_version", [], |r| r.get(0))?;
        if cipher.is_empty() {
            return Err(Error::Storage);
        }
        let version: u32 = connection.pragma_query_value(None, "user_version", |r| r.get(0))?;
        if version > 1 {
            return Err(Error::Storage);
        }
        connection.busy_timeout(std::time::Duration::from_secs(3))?;
        connection.execute_batch("PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL;
          BEGIN IMMEDIATE;
          CREATE TABLE IF NOT EXISTS operations(id TEXT PRIMARY KEY, idempotency_key TEXT UNIQUE NOT NULL, document TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS operation_events(id INTEGER PRIMARY KEY AUTOINCREMENT, document TEXT NOT NULL);
          PRAGMA user_version=1; COMMIT;")?;
        Ok(Self {
            connection: Mutex::new(connection),
            options,
        })
    }
    fn transaction<T>(&self, f: impl FnOnce(&Transaction<'_>) -> Result<T>) -> Result<T> {
        let mut conn = self.connection.lock().map_err(|_| Error::Storage)?;
        let start_id: i64 = conn.query_row(
            "SELECT coalesce(max(id),0) FROM operation_events",
            [],
            |row| row.get(0),
        )?;
        let tx = conn.transaction()?;
        let result = f(&tx)?;
        tx.commit()?;
        // Only committed events; a diagnostic failure never changes a successful business transaction.
        if let Err(_error) = copy_business_events(&conn, start_id) {
            tracing::warn!(event = "logs.business_copy_failed");
        }
        Ok(result)
    }
}
fn decode<T: serde::de::DeserializeOwned>(value: String) -> Result<T> {
    serde_json::from_str(&value).map_err(|_| Error::Storage)
}
fn encode(value: &impl serde::Serialize) -> Result<String> {
    serde_json::to_string(value).map_err(|_| Error::Storage)
}
fn get(tx: &Transaction<'_>, id: &str) -> Result<Operation> {
    let value = tx
        .query_row("SELECT document FROM operations WHERE id=?1", [id], |r| {
            r.get(0)
        })
        .optional()?;
    decode(value.ok_or(Error::NotFound)?)
}
fn save(tx: &Transaction<'_>, operation: &Operation) -> Result<()> {
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
impl Journal for SqlCipherJournal {
    fn accept(&self, key: &str, command: Command) -> Result<Operation> {
        if key.is_empty()
            || key.len() > 128
            || !key.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'-')
        {
            return Err(Error::Invalid);
        }
        match &command {
            Command::StartAudio { input_id, .. }
            | Command::EnrollVoice { input_id }
            | Command::StartVoiceProfileAudio { input_id, .. }
            | Command::EnrollVoiceProfile { input_id, .. }
                if input_id.is_empty() || input_id.len() > 512 =>
            {
                return Err(Error::Invalid);
            }
            _ => {}
        }
        match &command {
            Command::EnrollVoiceProfile {
                profile_id, name, ..
            } => crate::modules::personal_voice::domain::validate(profile_id, name)?,
            Command::StartVoiceProfileAudio {
                voice_profile_id, ..
            } if uuid::Uuid::parse_str(voice_profile_id).is_err() => return Err(Error::Invalid),
            _ => {}
        }
        let kind = command.kind();
        self.transaction(|tx| {
            let old: Option<String> = tx.query_row("SELECT document FROM operations WHERE idempotency_key=?1", [key], |r| r.get(0)).optional()?;
            if let Some(old) = old {
                let operation: Operation = decode(old)?;
                return if operation.command == command { Ok(operation) } else { Err(Error::Conflict) };
            }
            if !matches!(command, Command::CheckStorage) {
                let active: i64 = tx.query_row("SELECT count(*) FROM operations WHERE json_extract(document,'$.kind') != ?1 AND json_extract(document,'$.status') IN (?2,?3,?4)", params![OperationKind::StorageCheck.as_str(),Status::Accepted.as_str(),Status::Running.as_str(),Status::CancellationRequested.as_str()], |r| r.get(0))?;
                if active > 0 { return Err(Error::Busy); }
            }
            let total: i64 = tx.query_row("SELECT count(*) FROM operations", [], |r| r.get(0))?;
            let pending: i64 = tx.query_row("SELECT count(*) FROM operations WHERE json_extract(document,'$.status') IN (?1,?2,?3)",params![Status::Accepted.as_str(),Status::Running.as_str(),Status::CancellationRequested.as_str()], |r| r.get(0))?;
            if total >= self.options.max_operations || pending >= self.options.max_pending { return Err(Error::Capacity); }
            let operation = Operation { operation_id: uuid::Uuid::new_v4().to_string(), kind,
                command, status: Status::Accepted, detail: None };
            tx.execute("INSERT INTO operations VALUES (?1,?2,?3)", params![operation.operation_id, key, encode(&operation)?])?;
            save(tx, &operation)?;
            Ok(operation)
        })
    }
    fn get(&self, id: &str) -> Result<Operation> {
        self.transaction(|tx| get(tx, id))
    }
    fn recent(&self) -> Result<Vec<Operation>> {
        self.transaction(|tx| {
            let mut query =
                tx.prepare("SELECT document FROM operations ORDER BY rowid DESC LIMIT 100")?;
            query
                .query_map([], |r| r.get::<_, String>(0))?
                .map(|row| decode(row?))
                .collect()
        })
    }
    fn snapshot(&self) -> Result<(Vec<Operation>, i64)> {
        self.transaction(|tx| {
            let cursor = tx.query_row(
                "SELECT coalesce(max(id),0) FROM operation_events",
                [],
                |r| r.get(0),
            )?;
            let mut query =
                tx.prepare("SELECT document FROM operations ORDER BY rowid DESC LIMIT 100")?;
            let items = query
                .query_map([], |r| r.get::<_, String>(0))?
                .map(|row| decode(row?))
                .collect::<Result<Vec<Operation>>>()?;
            Ok((items, cursor))
        })
    }
    fn events(&self, after: i64) -> Result<Vec<Event>> {
        self.transaction(|tx| {
            let mut query = tx.prepare(
                "SELECT id,document FROM operation_events WHERE id>?1 ORDER BY id LIMIT ?2",
            )?;
            query
                .query_map(params![after, self.options.event_batch], |r| {
                    Ok((r.get::<_, i64>(0)?, r.get::<_, String>(1)?))
                })?
                .map(|row| {
                    let (id, document) = row?;
                    let mut event: Event = decode(document)?;
                    event.event_id = id;
                    Ok(event)
                })
                .collect()
        })
    }
    fn last_event_id(&self) -> Result<i64> {
        self.transaction(|tx| {
            Ok(tx.query_row(
                "SELECT coalesce(max(id),0) FROM operation_events",
                [],
                |r| r.get(0),
            )?)
        })
    }
    fn claim(&self) -> Result<Option<Operation>> {
        self.transaction(|tx| {
            let document: Option<String> = tx.query_row("SELECT document FROM operations WHERE json_extract(document,'$.status')=?1 ORDER BY rowid LIMIT 1", [Status::Accepted.as_str()], |r| r.get(0)).optional()?;
            let Some(document) = document else { return Ok(None); };
            let mut operation: Operation = decode(document)?;
            operation.status = Status::Running;
            save(tx, &operation)?;
            Ok(Some(operation))
        })
    }
    fn finish(&self, id: &str, result: Result<Completion>) -> Result<()> {
        self.transaction(|tx| {
            let mut operation = get(tx, id)?;
            if operation.status.terminal() {
                return Ok(());
            }
            (operation.status, operation.detail) = if operation.status
                == Status::CancellationRequested
                && !result
                    .as_ref()
                    .is_ok_and(|outcome| outcome.effect_committed)
            {
                (Status::Cancelled, None)
            } else {
                match result {
                    Ok(outcome) => (Status::Succeeded, Some(outcome.detail)),
                    Err(Error::Audio(code)) => (Status::Failed, Some(code.as_str().into())),
                    Err(_) => (Status::Failed, Some("processing_failed".into())),
                }
            };
            save(tx, &operation)
        })
    }
    fn cancel(&self, id: &str) -> Result<Operation> {
        self.transaction(|tx| {
            let mut operation = get(tx, id)?;
            if operation.status.terminal() || operation.status == Status::CancellationRequested {
                return Ok(operation);
            }
            operation.status = if operation.status == Status::Accepted {
                Status::Cancelled
            } else {
                Status::CancellationRequested
            };
            save(tx, &operation)?;
            Ok(operation)
        })
    }
    fn progress(&self, id: &str, detail: &str) -> Result<()> {
        self.transaction(|tx| {
            let mut operation = get(tx, id)?;
            if operation.status == Status::Running {
                operation.detail = Some(detail.into());
                save(tx, &operation)?;
            }
            Ok(())
        })
    }
    fn recover(&self) -> Result<()> {
        self.transaction(|tx| {
            // Fixed-size SQL batch, independent of the number of interrupted operations.
            // All identifiers/expressions are static. No client input forms SQL text.
            tx.execute_batch("CREATE TEMP TABLE IF NOT EXISTS operations_recovery(id TEXT PRIMARY KEY); DELETE FROM operations_recovery;")?;
            tx.execute("INSERT INTO operations_recovery SELECT id FROM operations WHERE json_extract(document,'$.status') IN (?1,?2)
              OR (json_extract(document,'$.status')=?3 AND json_extract(document,'$.kind') != ?4)",
              params![Status::Running.as_str(),Status::CancellationRequested.as_str(),Status::Accepted.as_str(),OperationKind::StorageCheck.as_str()])?;
            tx.execute("UPDATE operations SET document=json_set(document,'$.status',CASE WHEN json_extract(document,'$.status')=?1 THEN ?2 ELSE ?3 END,'$.detail',?4)
              WHERE id IN (SELECT id FROM operations_recovery)",params![Status::CancellationRequested.as_str(),Status::Cancelled.as_str(),Status::Interrupted.as_str(),SERVICE_RESTARTED])?;
            tx.execute("INSERT INTO operation_events(document) SELECT json_object('eventId',0,'eventType',CASE WHEN json_extract(document,'$.status')=?1 THEN ?2 ELSE ?3 END,
              'schemaVersion',1,'module','operations','operationId',id,'occurredAtUtc',strftime('%Y-%m-%dT%H:%M:%fZ','now'),'operation',json(document))
              FROM operations WHERE id IN (SELECT id FROM operations_recovery) ORDER BY rowid",
              params![Status::Cancelled.as_str(),event_name(Status::Cancelled),event_name(Status::Interrupted)])?;
            tx.execute("DELETE FROM operations_recovery",[])?;
            Ok(())
        })
    }
}

fn copy_business_events(connection: &Connection, after: i64) -> Result<()> {
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

const SERVICE_RESTARTED: &str = "service_restarted";
