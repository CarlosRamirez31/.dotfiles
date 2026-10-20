use crate::commons::{Error, Result};
use rusqlite::Connection;
use std::path::Path;

pub(super) fn open(path: &Path, key: &str) -> Result<Connection> {
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
    Ok(connection)
}
