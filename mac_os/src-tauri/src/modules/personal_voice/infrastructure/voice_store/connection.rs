use super::VoiceStore;
use crate::commons::{Error, Result};
use rusqlite::{Connection, OptionalExtension, TransactionBehavior, params};
use std::time::Duration;
impl VoiceStore {
    pub(super) fn connection(&self) -> Result<Connection> {
        let mut connection = Connection::open(&self.path)?;
        connection.pragma_update(None, "key", &self.key)?;
        connection.busy_timeout(Duration::from_secs(3))?;
        // Additive, atomic migration: transfer the single legacy embedding without overwriting it.
        let tx = connection.transaction_with_behavior(TransactionBehavior::Immediate)?;
        tx.execute_batch("CREATE TABLE IF NOT EXISTS personal_voice_profile(id INTEGER PRIMARY KEY CHECK(id=1), embedding TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS voice_profiles(id TEXT PRIMARY KEY, name TEXT NOT NULL, embedding TEXT NOT NULL,
              is_default INTEGER NOT NULL CHECK(is_default IN (0,1)), updated_at TEXT NOT NULL);
            CREATE UNIQUE INDEX IF NOT EXISTS voice_profiles_one_default ON voice_profiles(is_default) WHERE is_default=1;")?;
        let legacy: Option<String> = tx
            .query_row(
                "SELECT embedding FROM personal_voice_profile WHERE id=1",
                [],
                |r| r.get(0),
            )
            .optional()?;
        if let Some(embedding) = legacy {
            let count: i64 =
                tx.query_row("SELECT count(*) FROM voice_profiles", [], |r| r.get(0))?;
            // A mixed legacy/new database is ambiguous: preserve both tables and report an error.
            if count != 0 {
                return Err(Error::Storage);
            }
            tx.execute("INSERT INTO voice_profiles VALUES(?1,?2,?3,1,strftime('%Y-%m-%dT%H:%M:%fZ','now'))",
                params!["00000000-0000-4000-8000-000000000001", "Voz anterior", embedding])?;
            tx.execute("DELETE FROM personal_voice_profile WHERE id=1", [])?;
        }
        tx.commit()?;
        Ok(connection)
    }
}
