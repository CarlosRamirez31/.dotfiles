use crate::commons::{Command, Result};
use crate::modules::operations::domain::{Event, Operation, Status};
use std::sync::{
    Arc, Mutex,
    atomic::{AtomicBool, Ordering},
};
use tokio::sync::Notify;

pub trait Journal: Send + Sync {
    fn accept(&self, key: &str, command: Command) -> Result<Operation>;
    fn get(&self, id: &str) -> Result<Operation>;
    fn recent(&self) -> Result<Vec<Operation>>;
    fn events(&self, after: i64) -> Result<Vec<Event>>;
    fn last_event_id(&self) -> Result<i64>;
    fn claim(&self) -> Result<Option<Operation>>;
    fn finish(&self, id: &str, result: Result<Completion>) -> Result<()>;
    fn cancel(&self, id: &str) -> Result<Operation>;
    fn recover(&self) -> Result<()>;
    fn progress(&self, id: &str, detail: &str) -> Result<()>;
}

pub trait StorageCheck: Send + Sync {
    fn check(&self) -> Result<String>;
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
type ActiveCommand = Option<(String, Arc<AtomicBool>)>;

#[derive(Clone)]
pub struct Operations {
    pub journal: Arc<dyn Journal>,
    pub changed: Arc<Notify>,
    pub work: Arc<Notify>,
    active: Arc<Mutex<ActiveCommand>>,
}
impl Operations {
    pub fn new(journal: Arc<dyn Journal>) -> Self {
        Self {
            journal,
            changed: Arc::new(Notify::new()),
            work: Arc::new(Notify::new()),
            active: Arc::new(Mutex::new(None)),
        }
    }
    pub async fn accept(&self, key: String, command: Command) -> Result<Operation> {
        let journal = self.journal.clone();
        let result = blocking(move || journal.accept(&key, command)).await?;
        tracing::info!(event = "command.accepted", operation_id = %result.operation_id, kind = %result.kind);
        self.work.notify_one();
        self.changed.notify_waiters();
        Ok(result)
    }
    pub async fn cancel(&self, id: String) -> Result<Operation> {
        let journal = self.journal.clone();
        let lookup_id = id.clone();
        let operation = blocking(move || journal.cancel(&lookup_id)).await?;
        if let Some((active_id, cancelled)) = self
            .active
            .lock()
            .map_err(|_| crate::commons::Error::Storage)?
            .as_ref()
            && active_id == &id
        {
            cancelled.store(true, Ordering::Release);
        }
        tracing::info!(event = "command.cancel_requested", operation_id = %operation.operation_id);
        self.changed.notify_waiters();
        Ok(operation)
    }
    pub fn shutdown(&self) {
        if let Ok(active) = self.active.lock()
            && let Some((_, cancelled)) = active.as_ref()
        {
            cancelled.store(true, Ordering::Release);
        }
    }
    pub async fn run(self, handler: Arc<dyn CommandHandler>) -> Result<()> {
        let journal = self.journal.clone();
        blocking(move || journal.recover()).await?;
        loop {
            // Notify is only a wakeup. Accepted commands and their state live in the journal.
            let wakeup = self.work.notified();
            let journal = self.journal.clone();
            let Some(operation) = blocking(move || journal.claim()).await? else {
                wakeup.await;
                continue;
            };
            self.changed.notify_waiters();
            let cancelled = Arc::new(AtomicBool::new(false));
            *self
                .active
                .lock()
                .map_err(|_| crate::commons::Error::Storage)? =
                Some((operation.operation_id.clone(), cancelled.clone()));
            // Recheck after registration so a concurrent cancellation cannot be lost.
            let journal = self.journal.clone();
            let id = operation.operation_id.clone();
            if blocking(move || journal.get(&id)).await?.status == Status::CancellationRequested {
                cancelled.store(true, Ordering::Release);
            }
            tracing::info!(event = "command.started", operation_id = %operation.operation_id, kind = %operation.kind);
            let started = std::time::Instant::now();
            let handler = handler.clone();
            let command = operation.command.clone();
            let journal = self.journal.clone();
            let changed = self.changed.clone();
            let id = operation.operation_id.clone();
            let result = blocking(move || {
                handler.execute(command, cancelled, &|detail| {
                    journal.progress(&id, detail)?;
                    tracing::info!(event = "command.progress", operation_id = %id, code = detail);
                    changed.notify_waiters();
                    Ok(())
                })
            })
            .await;
            *self
                .active
                .lock()
                .map_err(|_| crate::commons::Error::Storage)? = None;
            if result.is_ok() {
                tracing::info!(event = "command.finished", operation_id = %operation.operation_id, elapsed_ms = started.elapsed().as_millis() as u64);
            } else {
                tracing::error!(event = "command.failed", operation_id = %operation.operation_id, elapsed_ms = started.elapsed().as_millis() as u64);
            }
            let journal = self.journal.clone();
            blocking(move || journal.finish(&operation.operation_id, result)).await?;
            self.changed.notify_waiters();
        }
    }
}

pub async fn blocking<T: Send + 'static>(
    job: impl FnOnce() -> Result<T> + Send + 'static,
) -> Result<T> {
    tokio::task::spawn_blocking(job)
        .await
        .map_err(|_| crate::commons::Error::Storage)?
}

pub fn event_name(status: Status) -> &'static str {
    match status {
        Status::Accepted => "operation.accepted",
        Status::Running => "operation.started",
        Status::CancellationRequested => "operation.cancellation_requested",
        Status::Succeeded => "operation.succeeded",
        Status::Failed => "operation.failed",
        Status::Cancelled => "operation.cancelled",
        Status::Interrupted => "operation.interrupted",
    }
}
