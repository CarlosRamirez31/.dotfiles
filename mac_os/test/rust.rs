#[path = "../src-tauri/src/modules/ai_rnnoise/test/mod.rs"]
mod ai_rnnoise;
#[path = "../src-tauri/src/modules/audio/test/mod.rs"]
mod audio;
#[path = "../src-tauri/src/commons/test/mod.rs"]
mod commons;
#[path = "../src-tauri/src/modules/operations/test/mod.rs"]
mod operations;
#[path = "../src-tauri/src/modules/personal_voice/test/mod.rs"]
mod personal_voice;
#[path = "support.rs"]
pub(crate) mod support;

#[cfg(unix)]
#[path = "../src-tauri/src/bootstrap/test/mod.rs"]
mod lifecycle;
