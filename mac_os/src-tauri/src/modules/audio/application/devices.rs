use crate::commons::{Result, utils::blocking};
use crate::modules::audio::domain::Devices;
use std::sync::Arc;

pub trait DeviceCatalog: Send + Sync {
    fn list(&self) -> Result<Devices>;
}

#[derive(Clone)]
pub struct DeviceService {
    catalog: Arc<dyn DeviceCatalog>,
}
impl DeviceService {
    pub fn new(catalog: Arc<dyn DeviceCatalog>) -> Self {
        Self { catalog }
    }
    pub async fn list(&self) -> Result<Devices> {
        let catalog = self.catalog.clone();
        blocking(move || catalog.list()).await
    }
}
