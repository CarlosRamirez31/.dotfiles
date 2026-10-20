use std::path::Path;
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
