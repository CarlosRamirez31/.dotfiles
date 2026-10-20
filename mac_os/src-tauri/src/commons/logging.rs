use serde::Deserialize;
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
/// Deletes only our dated regular files. Today's open rolling files are never eligible.
#[cfg(test)]
pub fn cleanup(directory: &Path, retention_days: u64, today: &str) -> std::io::Result<()> {
    cleanup_owned(
        directory,
        retention_days,
        today,
        &["host", "service", "business"],
        &[],
    )
}
pub(crate) fn cleanup_owned(
    directory: &Path,
    retention_days: u64,
    today: &str,
    owners: &[&str],
    active_days: &[u64],
) -> std::io::Result<()> {
    let now = std::time::SystemTime::now();
    if std::fs::symlink_metadata(directory)?
        .file_type()
        .is_symlink()
    {
        return Err(std::io::Error::other("unsafe_log_directory"));
    }
    for item in std::fs::read_dir(directory)? {
        let item = item?;
        let metadata = item.path().symlink_metadata()?;
        if !metadata.file_type().is_file() {
            continue;
        }
        let name = item.file_name();
        let Some(name) = name.to_str() else {
            continue;
        };
        let Some(date) = owners.iter().find_map(|prefix| {
            name.strip_prefix(&format!("{prefix}."))
                .and_then(|s| s.strip_suffix(".jsonl"))
        }) else {
            continue;
        };
        // tracing-appender uses YYYY-MM-DD. Use the partition date, not an arbitrary file count.
        if date.len() != 10
            || date.as_bytes()[4] != b'-'
            || date.as_bytes()[7] != b'-'
            || date == today
        {
            continue;
        }
        let Some(age) = partition_age_days(date, now) else {
            continue;
        };
        let current = now
            .duration_since(std::time::UNIX_EPOCH)
            .map_err(std::io::Error::other)?
            .as_secs()
            / 86400;
        if age > retention_days && !active_days.contains(&(current - age)) {
            std::fs::remove_file(item.path())?;
        }
    }
    Ok(())
}
fn partition_age_days(date: &str, now: std::time::SystemTime) -> Option<u64> {
    // Gregorian civil date -> days since epoch; validate by month length including leap years.
    let y: i64 = date.get(..4)?.parse().ok()?;
    let m: i64 = date.get(5..7)?.parse().ok()?;
    let d: i64 = date.get(8..)?.parse().ok()?;
    let leap = y % 4 == 0 && (y % 100 != 0 || y % 400 == 0);
    let limit = match m {
        2 => {
            if leap {
                29
            } else {
                28
            }
        }
        4 | 6 | 9 | 11 => 30,
        1 | 3 | 5 | 7 | 8 | 10 | 12 => 31,
        _ => return None,
    };
    if y < 1970 || !(1..=limit).contains(&d) {
        return None;
    }
    let year = y - i64::from(m <= 2);
    let era = year / 400;
    let yo = year - era * 400;
    let day = era * 146097 + yo * 365 + yo / 4 - yo / 100
        + (153 * (m + if m > 2 { -3 } else { 9 }) + 2) / 5
        + d
        - 1
        - 719468;
    let current = now.duration_since(std::time::UNIX_EPOCH).ok()?.as_secs() / 86400;
    current.checked_sub(day.try_into().ok()?)
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

/// The UI cannot submit free text, request bodies, tokens or arbitrary metadata to the log file.
#[derive(Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ClientEvent {
    Connected,
    RequestAccepted,
    ConnectionLost,
    RequestFailed,
    StartupFailed,
}
impl ClientEvent {
    pub fn code(&self) -> &'static str {
        match self {
            Self::RequestAccepted => "client.request_accepted",
            Self::Connected => "client.connected",
            Self::ConnectionLost => "client.connection_lost",
            Self::RequestFailed => "client.request_failed",
            Self::StartupFailed => "client.startup_failed",
        }
    }
}
#[tauri::command]
pub fn client_log(event: ClientEvent, operation_id: Option<String>) -> Result<(), String> {
    let operation_id = operation_id
        .map(|id| uuid::Uuid::parse_str(&id).map(|id| id.to_string()))
        .transpose()
        .map_err(|_| "invalid_log_correlation")?;
    match event {
        ClientEvent::Connected | ClientEvent::RequestAccepted => {
            tracing::info!(source = "client", event = event.code(), operation_id)
        }
        ClientEvent::ConnectionLost => {
            tracing::warn!(source = "client", event = event.code(), operation_id)
        }
        ClientEvent::RequestFailed | ClientEvent::StartupFailed => {
            tracing::error!(source = "client", event = event.code(), operation_id)
        }
    }
    Ok(())
}

const SERVICE_COMPONENT: &str = "service";
