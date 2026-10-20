use crate::commons::Result;
pub trait StorageCheck: Send + Sync {
    fn check(&self) -> Result<String>;
}
