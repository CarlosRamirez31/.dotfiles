mod codec;
mod connection;
mod diagnostics;
mod mutations;
mod queries;
mod records;
mod recovery;

use crate::commons::{Command, Error, Result};
use crate::modules::operations::{
    application::{Completion, Journal, validate_command},
    domain::{Event, Operation},
};
use rusqlite::{Connection, Transaction};
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
        let connection = connection::open(path, key)?;
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
        if let Err(_error) = diagnostics::copy_business_events(&conn, start_id) {
            tracing::warn!(event = "logs.business_copy_failed");
        }
        Ok(result)
    }
}
impl Journal for SqlCipherJournal {
    fn accept(&self, key: &str, command: Command) -> Result<Operation> {
        validate_command(key, &command)?;
        self.transaction(|tx| mutations::accept(tx, key, command, &self.options))
    }
    fn get(&self, id: &str) -> Result<Operation> {
        self.transaction(|tx| queries::get(tx, id))
    }
    fn recent(&self) -> Result<Vec<Operation>> {
        self.transaction(queries::recent)
    }
    fn snapshot(&self) -> Result<(Vec<Operation>, i64)> {
        self.transaction(queries::snapshot)
    }
    fn events(&self, after: i64) -> Result<Vec<Event>> {
        self.transaction(|tx| queries::events(tx, after, self.options.event_batch))
    }
    fn last_event_id(&self) -> Result<i64> {
        self.transaction(queries::last_event_id)
    }
    fn claim(&self) -> Result<Option<Operation>> {
        self.transaction(mutations::claim)
    }
    fn finish(&self, id: &str, result: Result<Completion>) -> Result<()> {
        self.transaction(|tx| mutations::finish(tx, id, result))
    }
    fn cancel(&self, id: &str) -> Result<Operation> {
        self.transaction(|tx| mutations::cancel(tx, id))
    }
    fn progress(&self, id: &str, detail: &str) -> Result<()> {
        self.transaction(|tx| mutations::progress(tx, id, detail))
    }
    fn recover(&self) -> Result<()> {
        self.transaction(recovery::recover)
    }
}
