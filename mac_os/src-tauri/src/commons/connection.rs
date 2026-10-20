use super::protocol;
use serde::{Deserialize, Serialize};
#[derive(Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ConnectionInfo {
    pub endpoint: String,
    pub token: String,
    pub protocol_version: u32,
    #[serde(default = "protocol::default_api_version")]
    pub api_version: String,
}
