use crate::{
    commons::{Error, Result},
    modules::operations::application::StorageCheck,
};
use std::path::PathBuf;

pub struct SqlCipherCheck {
    pub path: PathBuf,
    pub key: String,
}
impl StorageCheck for SqlCipherCheck {
    fn check(&self) -> Result<String> {
        let connection = rusqlite::Connection::open_with_flags(
            &self.path,
            rusqlite::OpenFlags::SQLITE_OPEN_READ_ONLY,
        )?;
        connection.pragma_update(None, "key", &self.key)?;
        connection.busy_timeout(std::time::Duration::from_secs(3))?;
        let mut statement = connection.prepare("PRAGMA integrity_check")?;
        let rows = statement.query_map([], |row| row.get::<_, String>(0))?;
        for row in rows {
            if row? != INTEGRITY_OK {
                return Err(Error::Storage);
            }
        }
        Ok("integrity_ok".into())
    }
}

const INTEGRITY_OK: &str = "ok";
