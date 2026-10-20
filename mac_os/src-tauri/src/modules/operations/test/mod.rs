use crate::tests::support::*;
#[test]
fn encrypted_journal_survives_reopen_and_rejects_wrong_key() {
    let database = Database::new();
    let journal = database.open();
    let operation = journal.accept("one", Command::CheckStorage).unwrap();
    drop(journal);
    assert_ne!(
        &std::fs::read(&database.path).unwrap()[..16],
        b"SQLite format 3\0"
    );
    assert!(SqlCipherJournal::open(&database.path, "wrong-key").is_err());
    let reopened = database.open();
    assert_eq!(
        reopened.get(&operation.operation_id).unwrap().status,
        Status::Accepted
    );
    assert_eq!(
        reopened.events(0).unwrap()[0].operation_id,
        operation.operation_id
    );
    assert_eq!(
        SqlCipherCheck {
            path: database.path.clone(),
            key: "test-key-not-production".into()
        }
        .check()
        .unwrap(),
        "integrity_ok"
    );
}

#[test]
fn acceptance_is_idempotent_bounded_and_cancellation_does_not_lose_races() {
    let database = Database::new();
    let journal = database.open();
    let first = journal.accept("same", Command::CheckStorage).unwrap();
    assert_eq!(
        journal
            .accept("same", Command::CheckStorage)
            .unwrap()
            .operation_id,
        first.operation_id
    );
    assert_eq!(journal.events(0).unwrap().len(), 1);
    for n in 1..16 {
        journal
            .accept(&format!("key-{n}"), Command::CheckStorage)
            .unwrap();
    }
    assert!(matches!(
        journal.accept("overflow", Command::CheckStorage),
        Err(Error::Capacity)
    ));
    let claimed = journal.claim().unwrap().unwrap();
    assert_eq!(
        journal.cancel(&claimed.operation_id).unwrap().status,
        Status::CancellationRequested
    );
    journal
        .finish(&claimed.operation_id, Ok(String::from("ok").into()))
        .unwrap();
    assert_eq!(
        journal.get(&claimed.operation_id).unwrap().status,
        Status::Cancelled
    );
    let pending = journal.accept("now-fits", Command::CheckStorage).unwrap();
    assert_eq!(
        journal.cancel(&pending.operation_id).unwrap().status,
        Status::Cancelled
    );
}

#[test]
fn recovery_does_not_restart_running_work_and_replay_uses_cursor() {
    let database = Database::new();
    let journal = database.open();
    let first = journal.accept("first", Command::CheckStorage).unwrap();
    journal.claim().unwrap();
    let second = journal.accept("second", Command::CheckStorage).unwrap();
    let cursor = journal.last_event_id().unwrap();
    drop(journal);
    let journal = database.open();
    journal.recover().unwrap();
    assert_eq!(
        journal.get(&first.operation_id).unwrap().status,
        Status::Interrupted
    );
    assert_eq!(
        journal.claim().unwrap().unwrap().operation_id,
        second.operation_id
    );
    let events = journal.events(cursor).unwrap();
    assert_eq!(events.len(), 2);
    assert!(events.iter().all(|event| event.event_id > cursor));
}

#[tokio::test]
async fn http_acceptance_precedes_worker_and_authentication_is_required() {
    let database = Database::new();
    let journal = database.open();
    let operations = Operations::new(journal.clone());
    let app = router(Bff {
        operations: operations.clone(),
        token: "test-token".into(),
        api_version: crate::commons::protocol::default_api_version(),
        voices: Arc::new(crate::modules::personal_voice::infrastructure::VoiceStore {
            path: database.path.clone(),
            key: "test-key-not-production".into(),
            max_profiles: 32,
        }),
    });
    let unauthorized = app
        .clone()
        .oneshot(
            Request::builder()
                .uri("/v1/operations")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(unauthorized.status(), StatusCode::UNAUTHORIZED);
    let forbidden = app
        .clone()
        .oneshot(
            request("GET", "/v1/operations")
                .header("Origin", "https://evil.example")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(forbidden.status(), StatusCode::FORBIDDEN);
    let response = app
        .clone()
        .oneshot(
            request("POST", "/v1/operations/storage-check")
                .header("Idempotency-Key", "http-test")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(response.status(), StatusCode::ACCEPTED);
    let operation: Operation =
        serde_json::from_slice(&to_bytes(response.into_body(), 8192).await.unwrap()).unwrap();
    assert_eq!(operation.status, Status::Accepted);
    assert_eq!(
        journal.get(&operation.operation_id).unwrap().status,
        Status::Accepted
    );
    let invalid = app
        .clone()
        .oneshot(
            request("GET", "/v1/events")
                .header("Last-Event-ID", "999")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(invalid.status(), StatusCode::BAD_REQUEST);
    let checker = Arc::new(SqlCipherCheck {
        path: database.path.clone(),
        key: "test-key-not-production".into(),
    });
    let worker = tokio::spawn(operations.run(Arc::new(TestHandler(checker))));
    tokio::time::timeout(Duration::from_secs(5), async {
        loop {
            if journal
                .get(&operation.operation_id)
                .unwrap()
                .status
                .terminal()
            {
                break;
            }
            tokio::time::sleep(Duration::from_millis(10)).await;
        }
    })
    .await
    .unwrap();
    assert_eq!(
        journal.get(&operation.operation_id).unwrap().status,
        Status::Succeeded
    );
    assert_eq!(
        journal
            .events(1)
            .unwrap()
            .iter()
            .map(|e| e.event_type.as_str())
            .collect::<Vec<_>>(),
        ["operation.started", "operation.succeeded"]
    );
    worker.abort();
}

#[test]
fn audio_commands_never_resume_after_restart_and_idempotency_checks_payload() {
    let database = Database::new();
    let journal = database.open();
    let command = Command::StartAudio {
        input_id: "device-a".into(),
        personal_voice: false,
    };
    let operation = journal.accept("start", command.clone()).unwrap();
    assert_eq!(
        journal.accept("start", command).unwrap().operation_id,
        operation.operation_id
    );
    assert!(matches!(
        journal.accept(
            "start",
            Command::StartAudio {
                input_id: "device-a".into(),
                personal_voice: true
            }
        ),
        Err(Error::Conflict)
    ));
    journal.recover().unwrap();
    assert_eq!(
        journal.get(&operation.operation_id).unwrap().status,
        Status::Interrupted
    );
    assert!(journal.claim().unwrap().is_none());
}

#[tokio::test]
async fn sse_replays_serialized_events_after_the_requested_cursor() {
    use std::io::{Read, Write};
    let database = Database::new();
    let journal = database.open();
    let operation = journal.accept("sse", Command::CheckStorage).unwrap();
    journal.claim().unwrap();
    journal
        .finish(&operation.operation_id, Ok(String::from("ok").into()))
        .unwrap();
    let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await.unwrap();
    let address = listener.local_addr().unwrap();
    let app = router(Bff {
        operations: Operations::new(journal),
        token: "test-token".into(),
        api_version: crate::commons::protocol::default_api_version(),
        voices: Arc::new(crate::modules::personal_voice::infrastructure::VoiceStore {
            path: database.path.clone(),
            key: "test-key-not-production".into(),
            max_profiles: 32,
        }),
    });
    let server = tokio::spawn(async move {
        axum::serve(listener, app).await.unwrap();
    });
    let response = tokio::task::spawn_blocking(move || {
        let mut socket = std::net::TcpStream::connect(address).unwrap();
        socket.set_read_timeout(Some(Duration::from_secs(3))).unwrap();
        write!(socket, "GET /v1/events HTTP/1.1\r\nHost: {address}\r\nAuthorization: Bearer test-token\r\nLast-Event-ID: 1\r\n\r\n").unwrap();
        let mut received = String::new();
        let mut buffer = [0; 4096];
        while !received.contains("operation.succeeded") {
            let count = socket.read(&mut buffer).unwrap();
            assert!(count > 0);
            received.push_str(&String::from_utf8_lossy(&buffer[..count]));
        }
        received
    }).await.unwrap();
    assert!(response.contains("text/event-stream"));
    assert!(response.contains("id: 2"));
    assert!(response.contains(&operation.operation_id));
    assert!(!response.contains("operation.accepted"));
    server.abort();
}

#[test]
fn sql_values_cannot_inject_statements_and_recovery_is_idempotent() {
    let database = Database::new();
    let journal = database.open();
    let literal = "device'; DROP TABLE operations; --";
    let operation = journal
        .accept(
            "safe",
            Command::StartAudio {
                input_id: literal.into(),
                personal_voice: false,
            },
        )
        .unwrap();
    assert!(matches!(journal.get("' OR 1=1 --"), Err(Error::NotFound)));
    assert!(matches!(
        journal.accept("x';--", Command::CheckStorage),
        Err(Error::Invalid)
    ));
    assert_eq!(
        journal.get(&operation.operation_id).unwrap().command,
        Command::StartAudio {
            input_id: literal.into(),
            personal_voice: false
        }
    );
    journal.recover().unwrap();
    let sequence = journal.last_event_id().unwrap();
    journal.recover().unwrap();
    assert_eq!(journal.last_event_id().unwrap(), sequence);
    let events = journal.events(0).unwrap();
    assert_eq!(events.len(), 2);
    assert!(events[1].event_id > events[0].event_id);
    assert_eq!(events[1].operation.status, Status::Interrupted);
}
#[test]
fn business_copy_contains_only_committed_allowlisted_metadata() {
    // Tracing callsite caches are process-wide; isolate subscriber assertions from parallel tests.
    if std::env::var_os("AUDIO_TEST_LOG_CHILD").is_none() {
        let output = std::process::Command::new(std::env::current_exe().unwrap())
            .args([
                "--exact",
                "tests::operations::business_copy_contains_only_committed_allowlisted_metadata",
                "--nocapture",
            ])
            .env("AUDIO_TEST_LOG_CHILD", "1")
            .output()
            .unwrap();
        assert!(
            output.status.success(),
            "{}",
            String::from_utf8_lossy(&output.stdout)
        );
        return;
    }
    use std::io::Write;
    use std::sync::Mutex;
    use tracing_subscriber::prelude::*;
    #[derive(Clone)]
    struct Writer(Arc<Mutex<Vec<u8>>>);
    impl Write for Writer {
        fn write(&mut self, bytes: &[u8]) -> std::io::Result<usize> {
            self.0.lock().unwrap().extend_from_slice(bytes);
            Ok(bytes.len())
        }
        fn flush(&mut self) -> std::io::Result<()> {
            Ok(())
        }
    }
    let output = Arc::new(Mutex::new(Vec::new()));
    let capture = output.clone();
    let subscriber = tracing_subscriber::registry().with(
        tracing_subscriber::fmt::layer()
            .json()
            .with_writer(move || Writer(capture.clone()))
            .with_filter(
                tracing_subscriber::filter::Targets::new()
                    .with_target("business", tracing::Level::INFO),
            ),
    );
    tracing::subscriber::with_default(subscriber, || {
        let db = Database::new();
        let journal = db.open();
        let command = Command::EnrollVoice {
            input_id: "sensitive-device".into(),
        };
        let operation = journal.accept("idempotent-key", command.clone()).unwrap();
        journal.accept("idempotent-key", command).unwrap();
        assert!(
            journal
                .accept("idempotent-key", Command::CheckStorage)
                .is_err()
        );
        let text = String::from_utf8(output.lock().unwrap().clone()).unwrap();
        assert_eq!(text.lines().count(), 1);
        assert!(text.contains(&operation.operation_id));
        assert!(text.contains("operation.accepted"));
        assert!(!text.contains("sensitive-device"));
        assert!(!text.contains("idempotent-key"));
        assert!(!text.contains("command"));
    });
}

#[tokio::test]
async fn shutdown_wakes_idle_worker_and_prevents_starting_queued_work() {
    let database = Database::new();
    let journal = database.open();
    let operations = Operations::new(journal.clone());
    operations.shutdown();
    let operation = journal
        .accept("pending-stop", Command::CheckStorage)
        .unwrap();
    let handler = Arc::new(TestHandler(Arc::new(SqlCipherCheck {
        path: database.path.clone(),
        key: "test-key-not-production".into(),
    })));
    tokio::time::timeout(Duration::from_secs(2), operations.run(handler))
        .await
        .unwrap()
        .unwrap();
    assert_eq!(
        journal.get(&operation.operation_id).unwrap().status,
        Status::Accepted
    );

    let empty = Database::new();
    let operations = Operations::new(empty.open());
    let worker = tokio::spawn(operations.clone().run(Arc::new(TestHandler(Arc::new(
        SqlCipherCheck {
            path: empty.path.clone(),
            key: "test-key-not-production".into(),
        },
    )))));
    tokio::time::sleep(Duration::from_millis(50)).await;
    operations.shutdown();
    tokio::time::timeout(Duration::from_secs(2), worker)
        .await
        .unwrap()
        .unwrap()
        .unwrap();
}

#[tokio::test]
async fn shutdown_waits_for_active_handler_and_persists_cancellation() {
    use std::sync::atomic::{AtomicBool, Ordering};
    struct BlockingHandler(Arc<AtomicBool>, Arc<AtomicBool>);
    impl crate::modules::operations::application::CommandHandler for BlockingHandler {
        fn execute(
            &self,
            _: Command,
            stop: Arc<AtomicBool>,
            _: &dyn Fn(&str) -> crate::commons::Result<()>,
        ) -> crate::commons::Result<crate::modules::operations::application::Completion> {
            self.0.store(true, Ordering::Release);
            let deadline = std::time::Instant::now() + Duration::from_secs(3);
            while !stop.load(Ordering::Acquire) && std::time::Instant::now() < deadline {
                std::thread::sleep(Duration::from_millis(5));
            }
            assert!(stop.load(Ordering::Acquire));
            self.1.store(true, Ordering::Release);
            Ok("stopped".to_string().into())
        }
    }
    let database = Database::new();
    let journal = database.open();
    let operation = journal
        .accept("active-stop", Command::CheckStorage)
        .unwrap();
    let operations = Operations::new(journal.clone());
    let started = Arc::new(AtomicBool::new(false));
    let released = Arc::new(AtomicBool::new(false));
    let worker = tokio::spawn(
        operations
            .clone()
            .run(Arc::new(BlockingHandler(started.clone(), released.clone()))),
    );
    tokio::time::timeout(Duration::from_secs(2), async {
        while !started.load(Ordering::Acquire) {
            tokio::time::sleep(Duration::from_millis(5)).await;
        }
    })
    .await
    .unwrap();
    operations.shutdown();
    tokio::time::timeout(Duration::from_secs(3), worker)
        .await
        .unwrap()
        .unwrap()
        .unwrap();
    assert!(released.load(Ordering::Acquire));
    assert_eq!(
        journal.get(&operation.operation_id).unwrap().status,
        Status::Cancelled
    );
}

#[tokio::test]
async fn configured_api_prefix_and_atomic_snapshot_cursor_are_consistent() {
    let database = Database::new();
    let journal = database.open();
    let original = journal
        .accept("snapshot-old", Command::CheckStorage)
        .unwrap();
    journal.claim().unwrap();
    journal
        .finish(&original.operation_id, Ok("ok".to_string().into()))
        .unwrap();
    let app = router(Bff {
        operations: Operations::new(journal.clone()),
        token: "test-token".into(),
        api_version: "v7".into(),
        voices: Arc::new(crate::modules::personal_voice::infrastructure::VoiceStore {
            path: database.path.clone(),
            key: "test-key-not-production".into(),
            max_profiles: 32,
        }),
    });
    let absent = app
        .clone()
        .oneshot(
            request("GET", "/v1/operations")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(absent.status(), StatusCode::NOT_FOUND);
    let snapshot = app
        .clone()
        .oneshot(
            request("GET", "/v7/operations")
                .header("X-Event-Cursor", "1")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(snapshot.status(), StatusCode::OK);
    let cursor: i64 = snapshot
        .headers()
        .get("X-Event-Cursor")
        .unwrap()
        .to_str()
        .unwrap()
        .parse()
        .unwrap();
    let rows: Vec<Operation> =
        serde_json::from_slice(&to_bytes(snapshot.into_body(), 8192).await.unwrap()).unwrap();
    assert_eq!(rows[0].status, Status::Succeeded);
    let accepted = app
        .oneshot(
            request("POST", "/v7/operations/storage-check")
                .header("Idempotency-Key", "snapshot-new")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(accepted.status(), StatusCode::ACCEPTED);
    assert!(
        accepted
            .headers()
            .get("Location")
            .unwrap()
            .to_str()
            .unwrap()
            .starts_with("/v7/operations/")
    );
    let events = journal.events(cursor).unwrap();
    assert_eq!(events.len(), 1);
    assert_eq!(events[0].operation.status, Status::Accepted);
}
