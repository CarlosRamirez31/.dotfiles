pub mod client;
mod retention;
#[cfg(test)]
pub use retention::cleanup;
pub(crate) use retention::cleanup_owned;
use std::path::Path;
use tracing_subscriber::{filter::Targets, prelude::*};

pub struct LogGuard {
    _writers: Vec<tracing_appender::non_blocking::WorkerGuard>,
    stop: Option<std::sync::mpsc::Sender<()>>,
    cleanup: Option<std::thread::JoinHandle<()>>,
}
impl Drop for LogGuard {
    fn drop(&mut self) {
        if let Some(stop) = self.stop.take() {
            let _ = stop.send(());
        }
        if let Some(thread) = self.cleanup.take() {
            let _ = thread.join();
        }
    }
}
struct TrackedWriter {
    file: tracing_appender::rolling::RollingFileAppender,
    day: std::sync::Arc<std::sync::Mutex<u64>>,
}
fn epoch_day() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs()
        / 86400
}
impl std::io::Write for TrackedWriter {
    fn write(&mut self, bytes: &[u8]) -> std::io::Result<usize> {
        let mut day = self
            .day
            .lock()
            .map_err(|_| std::io::Error::other("log_lock_failed"))?;
        let written = self.file.write(bytes)?;
        *day = epoch_day();
        Ok(written)
    }
    fn flush(&mut self) -> std::io::Result<()> {
        self.file.flush()
    }
}
pub fn initialize(
    directory: &Path,
    component: &str,
    options: &super::options::LoggingOptions,
) -> Result<LogGuard, Box<dyn std::error::Error>> {
    std::fs::create_dir_all(directory)?;
    if std::fs::symlink_metadata(directory)?
        .file_type()
        .is_symlink()
    {
        return Err("unsafe_log_directory".into());
    }
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        std::fs::set_permissions(directory, std::fs::Permissions::from_mode(0o700))?;
    }
    let technical_day = std::sync::Arc::new(std::sync::Mutex::new(epoch_day()));
    let business_day = std::sync::Arc::new(std::sync::Mutex::new(epoch_day()));
    let writer = |prefix: &str, day| -> Result<_, Box<dyn std::error::Error>> {
        let file = tracing_appender::rolling::Builder::new()
            .rotation(tracing_appender::rolling::Rotation::DAILY)
            .filename_prefix(prefix)
            .filename_suffix("jsonl")
            .build(directory)?;
        Ok(
            tracing_appender::non_blocking::NonBlockingBuilder::default()
                .buffered_lines_limit(256)
                .lossy(true)
                .finish(TrackedWriter { file, day }),
        )
    };
    let (technical, technical_guard) = writer(component, technical_day.clone())?;
    let mut writers = vec![technical_guard];
    let business_layer = if component == SERVICE_COMPONENT {
        let (business, guard) = writer("business", business_day.clone())?;
        writers.push(guard);
        Some(
            tracing_subscriber::fmt::layer()
                .json()
                .with_ansi(false)
                .with_writer(business)
                .with_filter(Targets::new().with_target("business", tracing::Level::INFO)),
        )
    } else {
        None
    };
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::fmt::layer()
                .json()
                .with_ansi(false)
                .with_writer(technical)
                .with_filter(Targets::new().with_target("mac_os_lib", tracing::Level::INFO)),
        )
        .with(business_layer)
        .try_init()?;
    let directory = directory.to_owned();
    let options = options.clone();
    let (stop, receiver) = std::sync::mpsc::channel();
    tracing::info!(event = "process.started", component);
    let component = component.to_owned();
    let cleanup = std::thread::spawn(move || {
        loop {
            let technical = technical_day.lock().expect("log_day_lock");
            let business = business_day.lock().expect("log_day_lock");
            let owners = if component == SERVICE_COMPONENT {
                vec!["service", "business"]
            } else {
                vec!["host"]
            };
            let active = if component == SERVICE_COMPONENT {
                vec![*technical, *business]
            } else {
                vec![*technical]
            };
            let result = cleanup_owned(&directory, options.retention_days, "", &owners, &active);
            drop(technical);
            drop(business);
            if result.is_err() {
                tracing::warn!(event = "logs.cleanup_failed");
            }
            match receiver.recv_timeout(std::time::Duration::from_secs(options.cleanup_seconds)) {
                Err(std::sync::mpsc::RecvTimeoutError::Timeout) => {}
                _ => break,
            }
        }
    });
    Ok(LogGuard {
        _writers: writers,
        stop: Some(stop),
        cleanup: Some(cleanup),
    })
}

const SERVICE_COMPONENT: &str = "service";
