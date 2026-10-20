use super::{Operations, blocking};
use crate::commons::{Error, Result};
use crate::modules::operations::domain::{Event, Operation};

impl Operations {
    pub async fn recent(&self) -> Result<Vec<Operation>> {
        let journal = self.journal.clone();
        blocking(move || journal.recent()).await
    }
    pub async fn snapshot(&self) -> Result<(Vec<Operation>, i64)> {
        let journal = self.journal.clone();
        blocking(move || journal.snapshot()).await
    }
    pub async fn get(&self, id: String) -> Result<Operation> {
        let journal = self.journal.clone();
        blocking(move || journal.get(&id)).await
    }
    pub async fn validate_cursor(&self, cursor: i64) -> Result<()> {
        let journal = self.journal.clone();
        let last = blocking(move || journal.last_event_id()).await?;
        if cursor < 0 || cursor > last {
            return Err(Error::Invalid);
        }
        Ok(())
    }
    pub async fn events_after(&self, cursor: i64) -> Result<Vec<Event>> {
        let journal = self.journal.clone();
        blocking(move || journal.events(cursor)).await
    }
}
