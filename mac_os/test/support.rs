pub(crate) use crate::{
    commons::{Command, Error},
    modules::{
        diagnostics::infrastructure::SqlCipherCheck,
        operations::{
            application::{Journal, Operations, StorageCheck},
            domain::{Operation, Status},
            infrastructure::SqlCipherJournal,
            presentation::{Bff, router},
        },
    },
};
pub(crate) use axum::{
    body::{Body, to_bytes},
    http::{Request, StatusCode},
};
pub(crate) use std::{path::PathBuf, sync::Arc, time::Duration};
pub(crate) use tower::ServiceExt;

pub(crate) struct Database {
    pub(crate) path: PathBuf,
}
impl Database {
    pub(crate) fn new() -> Self {
        let directory =
            std::env::temp_dir().join(format!("microphone-test-{}", uuid::Uuid::new_v4()));
        std::fs::create_dir(&directory).unwrap();
        Self {
            path: directory.join("test.db"),
        }
    }
    pub(crate) fn open(&self) -> Arc<SqlCipherJournal> {
        Arc::new(SqlCipherJournal::open(&self.path, "test-key-not-production").unwrap())
    }
}
impl Drop for Database {
    fn drop(&mut self) {
        let _ = std::fs::remove_dir_all(self.path.parent().unwrap());
    }
}
pub(crate) fn request(method: &str, path: &str) -> axum::http::request::Builder {
    Request::builder()
        .method(method)
        .uri(path)
        .header("Authorization", "Bearer test-token")
}

pub(crate) struct TestHandler(pub(crate) Arc<SqlCipherCheck>);
impl crate::modules::operations::application::CommandHandler for TestHandler {
    fn execute(
        &self,
        _: Command,
        _: Arc<std::sync::atomic::AtomicBool>,
        _: &dyn Fn(&str) -> crate::commons::Result<()>,
    ) -> crate::commons::Result<crate::modules::operations::application::Completion> {
        self.0.check().map(Into::into)
    }
}
