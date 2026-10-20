use serde::{Deserialize, Serialize};
#[derive(Clone, Serialize, Deserialize)]
pub struct OperationsOptions {
    pub max_pending: i64,
    pub max_operations: i64,
    pub event_batch: i64,
}
impl Default for OperationsOptions {
    fn default() -> Self {
        Self {
            max_pending: 16,
            max_operations: 10000,
            event_batch: 64,
        }
    }
}
