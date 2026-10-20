use serde::{Deserialize, Serialize};
use std::path::PathBuf;

#[derive(Serialize, Deserialize)]
pub(super) struct Launch {
    pub options: crate::commons::options::Options,
    pub directory: PathBuf,
    pub token: String,
    pub voice_runtime: PathBuf,
    pub voice_script: PathBuf,
}
