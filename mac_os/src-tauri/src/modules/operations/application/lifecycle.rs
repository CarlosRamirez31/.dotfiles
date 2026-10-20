use super::Completion;
use crate::commons::{Error, Result};
use crate::modules::operations::domain::{Operation, Status};
const PROCESSING_FAILED: &str = "processing_failed";
pub(crate) fn complete(operation: &mut Operation, result: Result<Completion>) -> bool {
    if operation.status.terminal() {
        return false;
    }
    (operation.status, operation.detail) = if operation.status == Status::CancellationRequested
        && !result
            .as_ref()
            .is_ok_and(|outcome| outcome.effect_committed)
    {
        (Status::Cancelled, None)
    } else {
        match result {
            Ok(outcome) => (Status::Succeeded, Some(outcome.detail)),
            Err(Error::Audio(code)) => (Status::Failed, Some(code.as_str().into())),
            Err(_) => (Status::Failed, Some(PROCESSING_FAILED.into())),
        }
    };
    true
}

pub(crate) fn request_cancel(operation: &mut Operation) -> bool {
    if operation.status.terminal() || operation.status == Status::CancellationRequested {
        return false;
    }
    operation.status = if operation.status == Status::Accepted {
        Status::Cancelled
    } else {
        Status::CancellationRequested
    };
    true
}
