use crate::commons::AudioErrorCode;
use crate::commons::{Error, Result};
use crate::modules::operations::domain::{OperationKind, Status};
use crate::modules::personal_voice::{
    application::VoiceProfiles,
    domain::{VoiceProfile, validate},
};
use rusqlite::{Connection, OptionalExtension, TransactionBehavior, params};
use std::{path::PathBuf, time::Duration};

pub struct VoiceStore {
    pub path: PathBuf,
    pub key: String,
    pub max_profiles: usize,
}
impl VoiceStore {
    fn connection(&self) -> Result<Connection> {
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
fn idle(connection: &Connection) -> Result<()> {
    let active: i64 = connection.query_row("SELECT count(*) FROM operations WHERE json_extract(document,'$.kind') != ?1 AND json_extract(document,'$.status') IN (?2,?3,?4)", params![OperationKind::StorageCheck.as_str(),Status::Accepted.as_str(),Status::Running.as_str(),Status::CancellationRequested.as_str()], |r| r.get(0))?;
    if active != 0 {
        return Err(Error::Busy);
    }
    Ok(())
}
fn decode(document: String) -> Result<Vec<f32>> {
    let value: Vec<f32> = serde_json::from_str(&document).map_err(|_| Error::Storage)?;
    if value.len() != 192 || value.iter().any(|x| !x.is_finite()) {
        return Err(Error::Storage);
    }
    Ok(value)
}
impl VoiceProfiles for VoiceStore {
    fn list(&self) -> Result<Vec<VoiceProfile>> {
        let connection = self.connection()?;
        let mut query = connection.prepare("SELECT id,name,is_default,updated_at FROM voice_profiles ORDER BY is_default DESC,updated_at DESC,id")?;
        query
            .query_map([], |r| {
                Ok(VoiceProfile {
                    id: r.get(0)?,
                    name: r.get(1)?,
                    is_default: r.get(2)?,
                    updated_at: r.get(3)?,
                })
            })?
            .collect::<std::result::Result<Vec<_>, _>>()
            .map_err(Into::into)
    }
    fn embedding(&self, id: &str) -> Result<Vec<f32>> {
        let document: Option<String> = self
            .connection()?
            .query_row(
                "SELECT embedding FROM voice_profiles WHERE id=?1",
                [id],
                |r| r.get(0),
            )
            .optional()?;
        decode(document.ok_or(Error::NotFound)?)
    }
    fn save_profile(&self, id: &str, name: &str, embedding: &[f32], replace: bool) -> Result<()> {
        validate(id, name)?;
        if embedding.len() != 192 || embedding.iter().any(|x| !x.is_finite()) {
            return Err(Error::Invalid);
        }
        let document = serde_json::to_string(embedding).map_err(|_| Error::Storage)?;
        let mut connection = self.connection()?;
        let tx = connection.transaction_with_behavior(TransactionBehavior::Immediate)?;
        if replace {
            if tx.execute("UPDATE voice_profiles SET name=?2,embedding=?3,updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=?1",params![id,name.trim(),document])? == 0 { return Err(Error::NotFound); }
        } else {
            let count: i64 =
                tx.query_row("SELECT count(*) FROM voice_profiles", [], |r| r.get(0))?;
            if count >= self.max_profiles as i64 {
                return Err(Error::Audio(AudioErrorCode::VoiceProfileCapacity));
            }
            let exists: bool = tx.query_row(
                "SELECT EXISTS(SELECT 1 FROM voice_profiles WHERE id=?1)",
                [id],
                |r| r.get(0),
            )?;
            if exists {
                return Err(Error::Conflict);
            }
            tx.execute("INSERT INTO voice_profiles VALUES(?1,?2,?3,?4,strftime('%Y-%m-%dT%H:%M:%fZ','now'))",params![id,name.trim(),document,count==0])?;
        }
        tx.commit()?;
        tracing::info!(target:"business", event_type="voice_profile.saved", profile_id=id, replaced=replace);
        Ok(())
    }
    fn set_default(&self, id: &str) -> Result<()> {
        let mut connection = self.connection()?;
        let tx = connection.transaction_with_behavior(TransactionBehavior::Immediate)?;
        idle(&tx)?;
        let exists: bool = tx.query_row(
            "SELECT EXISTS(SELECT 1 FROM voice_profiles WHERE id=?1)",
            [id],
            |r| r.get(0),
        )?;
        if !exists {
            return Err(Error::NotFound);
        }
        tx.execute(
            "UPDATE voice_profiles SET is_default=0 WHERE is_default=1",
            [],
        )?;
        tx.execute("UPDATE voice_profiles SET is_default=1 WHERE id=?1", [id])?;
        tx.commit()?;
        tracing::info!(target:"business",event_type="voice_profile.default_changed",profile_id=id);
        Ok(())
    }
    fn delete(&self, id: &str) -> Result<()> {
        let mut connection = self.connection()?;
        let tx = connection.transaction_with_behavior(TransactionBehavior::Immediate)?;
        idle(&tx)?;
        let is_default: Option<bool> = tx
            .query_row(
                "SELECT is_default FROM voice_profiles WHERE id=?1",
                [id],
                |r| r.get(0),
            )
            .optional()?;
        // Deletion retries are harmless and never remove a different voice.
        let Some(is_default) = is_default else {
            return Ok(());
        };
        let count: i64 = tx.query_row("SELECT count(*) FROM voice_profiles", [], |r| r.get(0))?;
        if is_default && count > 1 {
            return Err(Error::Audio(AudioErrorCode::ChooseAnotherDefaultVoice));
        }
        tx.execute("DELETE FROM voice_profiles WHERE id=?1", [id])?;
        tx.commit()?;
        tracing::info!(target:"business",event_type="voice_profile.deleted",profile_id=id);
        Ok(())
    }
    fn load(&self) -> Result<Vec<f32>> {
        let id: Option<String> = self
            .connection()?
            .query_row(
                "SELECT id FROM voice_profiles WHERE is_default=1",
                [],
                |r| r.get(0),
            )
            .optional()?;
        self.embedding(&id.ok_or(Error::Audio(AudioErrorCode::VoiceEnrollmentRequired))?)
    }
    fn save(&self, embedding: &[f32]) -> Result<()> {
        let profiles = self.list()?;
        match profiles.as_slice() {
            [] => self.save_profile(
                &uuid::Uuid::new_v4().to_string(),
                "Mi voz",
                embedding,
                false,
            ),
            [one] => self.save_profile(&one.id, &one.name, embedding, true),
            _ => Err(Error::Audio(AudioErrorCode::VoiceSelectionRequired)),
        }
    }
}
