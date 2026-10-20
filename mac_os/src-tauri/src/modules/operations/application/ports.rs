use crate::commons::{Command, Result};
use crate::modules::operations::domain::{Event, Operation};
use std::sync::{Arc, atomic::AtomicBool};
pub trait Journal: Send + Sync {
    fn accept(&self, key: &str, command: Command) -> Result<Operation>;
    fn get(&self, id: &str) -> Result<Operation>;
    fn recent(&self) -> Result<Vec<Operation>>;
    fn snapshot(&self) -> Result<(Vec<Operation>, i64)>;
    fn events(&self, after: i64) -> Result<Vec<Event>>;
    fn last_event_id(&self) -> Result<i64>;
    fn claim(&self) -> Result<Option<Operation>>;
    fn finish(&self, id: &str, result: Result<Completion>) -> Result<()>;
    fn cancel(&self, id: &str) -> Result<Operation>;
    fn recover(&self) -> Result<()>;
    fn progress(&self, id: &str, detail: &str) -> Result<()>;
}

pub struct Completion {
    pub detail: String,
    pub effect_committed: bool,
}
impl From<String> for Completion {
    fn from(detail: String) -> Self {
        Self {
            detail,
            effect_committed: false,
        }
    }
}

pub trait CommandHandler: Send + Sync {
    fn execute(
        &self,
        command: Command,
        cancelled: Arc<AtomicBool>,
        progress: &dyn Fn(&str) -> Result<()>,
    ) -> Result<Completion>;
}
