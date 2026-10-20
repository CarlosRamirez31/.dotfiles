use crate::commons::{Error, Result};
use std::{path::PathBuf, time::Duration};

pub struct VoiceStore {
    pub path: PathBuf,
    pub key: String,
}
impl VoiceStore {
    fn connection(&self) -> Result<rusqlite::Connection> {
        let connection = rusqlite::Connection::open(&self.path)?;
        connection.pragma_update(None, "key", &self.key)?;
        connection.busy_timeout(Duration::from_secs(3))?;
        connection.execute("CREATE TABLE IF NOT EXISTS personal_voice_profile(id INTEGER PRIMARY KEY CHECK(id=1), embedding TEXT NOT NULL)", [])?;
        Ok(connection)
    }
    pub fn load(&self) -> Result<Vec<f32>> {
        use rusqlite::OptionalExtension;
        let document: Option<String> = self
            .connection()?
            .query_row(
                "SELECT embedding FROM personal_voice_profile WHERE id=1",
                [],
                |row| row.get(0),
            )
            .optional()?;
        let embedding: Vec<f32> =
            serde_json::from_str(&document.ok_or(Error::Audio("voice_enrollment_required"))?)
                .map_err(|_| Error::Storage)?;
        if embedding.len() != 192 || !embedding.iter().all(|x| x.is_finite()) {
            return Err(Error::Storage);
        }
        Ok(embedding)
    }
    pub fn save(&self, embedding: &[f32]) -> Result<()> {
        if embedding.len() != 192 || !embedding.iter().all(|x| x.is_finite()) {
            return Err(Error::Invalid);
        }
        let document = serde_json::to_string(embedding).map_err(|_| Error::Storage)?;
        self.connection()?.execute("INSERT INTO personal_voice_profile VALUES(1,?1) ON CONFLICT(id) DO UPDATE SET embedding=excluded.embedding", [document])?;
        Ok(())
    }
}
