use crate::{
    commons::{Command, Error},
    modules::{
        diagnostics::infrastructure::SqlCipherCheck,
        operations::{
            application::{Journal, Operations, StorageCheck},
            domain::{Operation, Status},
            infrastructure::SqlCipherJournal,
            presentation::{Bff, router},
        },
    },
};
use axum::{
    body::{Body, to_bytes},
    http::{Request, StatusCode},
};
use std::{path::PathBuf, sync::Arc, time::Duration};
use tower::ServiceExt;

struct Database {
    path: PathBuf,
}
impl Database {
    fn new() -> Self {
        let directory =
            std::env::temp_dir().join(format!("microphone-test-{}", uuid::Uuid::new_v4()));
        std::fs::create_dir(&directory).unwrap();
        Self {
            path: directory.join("test.db"),
        }
    }
    fn open(&self) -> Arc<SqlCipherJournal> {
        Arc::new(SqlCipherJournal::open(&self.path, "test-key-not-production").unwrap())
    }
}
impl Drop for Database {
    fn drop(&mut self) {
        let _ = std::fs::remove_dir_all(self.path.parent().unwrap());
    }
}
fn request(method: &str, path: &str) -> axum::http::request::Builder {
    Request::builder()
        .method(method)
        .uri(path)
        .header("Authorization", "Bearer test-token")
}

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

struct TestHandler(Arc<SqlCipherCheck>);
impl crate::modules::operations::application::CommandHandler for TestHandler {
    fn execute(
        &self,
        _: Command,
        _: Arc<std::sync::atomic::AtomicBool>,
        _: &dyn Fn(&str) -> crate::commons::Result<()>,
    ) -> crate::commons::Result<crate::modules::operations::application::Completion> {
        self.0.check().map(Into::into)
    }
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

#[test]
fn rnnoise_executes_embedded_network_and_preserves_normalized_pcm() {
    use crate::modules::audio::application::NoiseReducer;
    let mut processor = crate::modules::ai_rnnoise::infrastructure::RnNoise::default();
    let mut output = [0.0; 480];
    let mut seed = 7_u32;
    for _ in 0..100 {
        let input = std::array::from_fn(|_| {
            seed = seed.wrapping_mul(1664525).wrapping_add(1013904223);
            ((seed >> 8) as f32 / 16777216.0 - 0.5) * 0.1
        });
        processor.process(&input, &mut output);
        assert!(output.iter().all(|x| x.is_finite() && x.abs() <= 1.0));
    }
    assert!(output.iter().any(|x| x.abs() > 0.0));
}

#[test]
fn downsample_preserves_block_continuity_and_suppresses_aliasing() {
    use crate::modules::audio::infrastructure::Downsample;
    let signal: Vec<f32> = (0..4800)
        .map(|i| (2.0 * std::f32::consts::PI * 12000.0 * i as f32 / 48000.0).sin())
        .collect();
    let mut whole = Vec::new();
    Downsample::default().process(&signal, &mut whole);
    let mut split = Vec::new();
    let mut converter = Downsample::default();
    for chunk in signal.chunks(77) {
        converter.process(chunk, &mut split);
    }
    assert_eq!(split, whole);
    assert_eq!(whole.len(), 1600);
    let rms = (whole[100..].iter().map(|x| x * x).sum::<f32>() / 1500.0).sqrt();
    assert!(rms < 0.01, "Aliased 12 kHz energy: {rms}");
}

#[test]
fn voice_embedding_is_persisted_inside_the_encrypted_database() {
    let database = Database::new();
    let _journal = database.open();
    let store = crate::modules::personal_voice::infrastructure::VoiceStore {
        path: database.path.clone(),
        key: "test-key-not-production".into(),
    };
    assert!(matches!(
        store.load(),
        Err(Error::Audio("voice_enrollment_required"))
    ));
    assert!(store.save(&[f32::NAN; 192]).is_err());
    store.save(&[0.125; 192]).unwrap();
    assert_eq!(store.load().unwrap(), vec![0.125; 192]);
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
#[ignore = "Requires the private arm64 model runtime; no microphone is opened"]
fn real_personal_voice_adapter_roundtrip() {
    use crate::modules::{
        audio::application::PersonalVoice, personal_voice::infrastructure::NomoWorker,
    };
    let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap();
    let runtime = root.join(".runtime/personal-voice");
    let script = root.join("runtime/personal-voice/worker.py");
    let stop = Arc::new(std::sync::atomic::AtomicBool::new(false));
    let mut enrollment = NomoWorker::start(&runtime, &script, stop.clone(), None).unwrap();
    let pcm: Vec<f32> = (0..160_000)
        .map(|i| 0.05 * (i as f32 * 440.0 * 2.0 * std::f32::consts::PI / 16_000.0).sin())
        .collect();
    let embedding = enrollment.enroll(&pcm).unwrap();
    assert_eq!(embedding.len(), 192);
    drop(enrollment);
    let mut worker = NomoWorker::start(&runtime, &script, stop, Some(&embedding)).unwrap();
    let probability = worker.probability(&pcm[..2560]).unwrap();
    assert!((0.0..=1.0).contains(&probability));
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
