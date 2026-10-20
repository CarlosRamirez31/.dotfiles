use crate::tests::support::*;
#[test]
fn client_logging_rejects_free_text_and_non_uuid_metadata() {
    use crate::commons::logging::{ClientEvent, client_log};
    assert!(serde_json::from_str::<ClientEvent>("\"Bearer secret\"").is_err());
    assert!(
        client_log(
            ClientEvent::RequestAccepted,
            Some("private voice sample".into())
        )
        .is_err()
    );
    assert!(client_log(ClientEvent::Connected, None).is_ok());
}
#[test]
fn options_validate_precedence_and_reject_unknown_or_unsafe_values() {
    use crate::commons::options::Options;
    let file = [("MIC_LOG_RETENTION_DAYS".into(), "60".into())].into();
    let env = [("MIC_LOG_RETENTION_DAYS".into(), "30".into())].into();
    assert_eq!(
        Options::from_values(file, env)
            .unwrap()
            .logging
            .retention_days,
        30
    );
    for (key, value) in [
        ("MIC_VOICE_THRESHOLD", "NaN"),
        ("MIC_LOG_RETENTION_DAYS", "0"),
        ("MIC_VOICE_RUNTIME", "relative"),
        ("MIC_SECRET", "anything"),
        ("MIC_MAX_PENDING", "99999999999999999999"),
    ] {
        assert!(
            Options::from_values(Default::default(), [(key.into(), value.into())].into()).is_err()
        );
    }
}
#[test]
fn cleanup_removes_only_expired_owned_partitions_not_symlinks_or_unrelated_files() {
    let db = Database::new();
    let directory = db.path.parent().unwrap();
    for name in [
        "host.2000-01-01.jsonl",
        "business.2000-01-01.jsonl",
        "service.2999-01-01.jsonl",
        "user.2000-01-01.jsonl",
        "service.2000-99-01.jsonl",
    ] {
        std::fs::write(directory.join(name), "private").unwrap();
    }
    #[cfg(unix)]
    std::os::unix::fs::symlink(
        directory.join("user.2000-01-01.jsonl"),
        directory.join("service.2000-01-01.jsonl"),
    )
    .unwrap();
    crate::commons::logging::cleanup(directory, 30, "").unwrap();
    assert!(!directory.join("host.2000-01-01.jsonl").exists());
    assert!(!directory.join("business.2000-01-01.jsonl").exists());
    assert!(directory.join("service.2999-01-01.jsonl").exists());
    assert!(directory.join("user.2000-01-01.jsonl").exists());
    assert!(directory.join("service.2000-99-01.jsonl").exists());
    #[cfg(unix)]
    assert!(directory.join("service.2000-01-01.jsonl").is_symlink());
}
#[test]
fn env_parser_handles_quotes_and_rejects_duplicate_or_malformed_assignments() {
    use crate::commons::options::read_env;
    let db = Database::new();
    std::fs::write(
        &db.path,
        "# sample\nMIC_VOICE_THRESHOLD='0.8'\nMIC_MAX_PENDING=8\n",
    )
    .unwrap();
    let values = read_env(&db.path).unwrap();
    assert_eq!(values["MIC_VOICE_THRESHOLD"], "0.8");
    for text in [
        "MIC_MAX_PENDING=8\nMIC_MAX_PENDING=9",
        "MIC_MAX_PENDING",
        "MIC_MAX_PENDING='8",
    ] {
        std::fs::write(&db.path, text).unwrap();
        assert!(read_env(&db.path).is_err());
    }
}

#[test]
fn cleanup_preserves_open_partitions_and_other_process_files() {
    let db = Database::new();
    let directory = db.path.parent().unwrap();
    for name in ["host.2000-01-01.jsonl", "service.2000-01-01.jsonl"] {
        std::fs::write(directory.join(name), "data").unwrap();
    }
    crate::commons::logging::cleanup_owned(directory, 30, "", &["host"], &[10957]).unwrap();
    assert!(directory.join("host.2000-01-01.jsonl").exists());
    crate::commons::logging::cleanup_owned(directory, 30, "", &["host"], &[]).unwrap();
    assert!(!directory.join("host.2000-01-01.jsonl").exists());
    assert!(directory.join("service.2000-01-01.jsonl").exists());
}
#[test]
fn logger_writes_separate_files_and_cleans_at_startup() {
    if std::env::var_os("AUDIO_TEST_FILE_LOG_CHILD").is_none() {
        let output = std::process::Command::new(std::env::current_exe().unwrap())
            .args([
                "--exact",
                "tests::commons::logger_writes_separate_files_and_cleans_at_startup",
                "--nocapture",
            ])
            .env("AUDIO_TEST_FILE_LOG_CHILD", "1")
            .output()
            .unwrap();
        assert!(
            output.status.success(),
            "{}",
            String::from_utf8_lossy(&output.stdout)
        );
        return;
    }
    let db = Database::new();
    let directory = db.path.parent().unwrap().join("logs");
    std::fs::create_dir(&directory).unwrap();
    let expired = directory.join("service.2000-01-01.jsonl");
    std::fs::write(&expired, "expired").unwrap();
    let guard =
        crate::commons::logging::initialize(&directory, "service", &Default::default()).unwrap();
    tracing::info!(event = "technical_probe");
    tracing::info!(target:"business",event_type="operation.succeeded",operation_id="probe");
    let until = std::time::Instant::now() + Duration::from_secs(5);
    while expired.exists() && std::time::Instant::now() < until {
        std::thread::sleep(Duration::from_millis(10));
    }
    assert!(!expired.exists());
    drop(guard);
    let mut technical = String::new();
    let mut business = String::new();
    for file in std::fs::read_dir(&directory).unwrap() {
        let file = file.unwrap();
        let name = file.file_name();
        let name = name.to_string_lossy();
        if name.starts_with("service.") {
            technical.push_str(&std::fs::read_to_string(file.path()).unwrap());
        }
        if name.starts_with("business.") {
            business.push_str(&std::fs::read_to_string(file.path()).unwrap());
        }
    }
    assert!(technical.contains("technical_probe"));
    assert!(!technical.contains("operation.succeeded"));
    assert!(business.contains("operation.succeeded"));
    assert!(!business.contains("technical_probe"));
}
