use crate::commons::AudioErrorCode;
use crate::modules::personal_voice::application::VoiceProfiles;
use crate::tests::support::*;
#[test]
fn voice_embedding_is_persisted_inside_the_encrypted_database() {
    let database = Database::new();
    let _journal = database.open();
    let store = crate::modules::personal_voice::infrastructure::VoiceStore {
        path: database.path.clone(),
        key: "test-key-not-production".into(),
        max_profiles: 32,
    };
    assert!(matches!(
        store.load(),
        Err(Error::Audio(AudioErrorCode::VoiceEnrollmentRequired))
    ));
    assert!(store.save(&[f32::NAN; 192]).is_err());
    store.save(&[0.125; 192]).unwrap();
    assert_eq!(store.load().unwrap(), vec![0.125; 192]);
}

#[test]
#[ignore = "Requires the private arm64 model runtime; no microphone is opened"]
fn real_personal_voice_adapter_roundtrip() {
    use crate::modules::personal_voice::{
        application::{EnrollmentFactory, PersonalVoiceFactory},
        infrastructure::NomoFactory,
    };
    let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap();
    let runtime = root.join(".runtime/personal-voice");
    let script = root.join("runtime/personal-voice/worker.py");
    let stop = Arc::new(std::sync::atomic::AtomicBool::new(false));
    let factory = NomoFactory::new(runtime, script, Default::default());
    let enrollment_port: &dyn EnrollmentFactory = &factory;
    let filtering_port: &dyn PersonalVoiceFactory = &factory;
    let mut enrollment = enrollment_port.prepare_enrollment(stop.clone()).unwrap();
    assert!(matches!(
        enrollment.enroll(&[]),
        Err(crate::modules::audio::domain::capability::CapabilityError::InvalidInput)
    ));
    let pcm: Vec<f32> = (0..160_000)
        .map(|i| 0.05 * (i as f32 * 440.0 * 2.0 * std::f32::consts::PI / 16_000.0).sin())
        .collect();
    let embedding = enrollment.enroll(&pcm).unwrap();
    assert_eq!(embedding.len(), 192);
    drop(enrollment);
    let mut worker = filtering_port
        .prepare_filter(stop.clone(), &embedding)
        .unwrap();
    let probability = worker.probability(&pcm[..2560]).unwrap();
    assert!((0.0..=1.0).contains(&probability));
    stop.store(true, std::sync::atomic::Ordering::Release);
    assert!(matches!(
        worker.probability(&pcm[..2560]),
        Err(crate::modules::audio::domain::capability::CapabilityError::Cancelled)
    ));
}

#[test]
fn enrollment_factory_returns_typed_failure_without_installed_runtime() {
    use crate::modules::{
        audio::domain::capability::CapabilityError,
        personal_voice::{application::EnrollmentFactory, infrastructure::NomoFactory},
    };
    let directory = Database::new();
    let factory = NomoFactory::new(
        directory.path.clone(),
        directory.path.clone(),
        Default::default(),
    );
    let port: &dyn EnrollmentFactory = &factory;
    let result = port.prepare_enrollment(Arc::new(std::sync::atomic::AtomicBool::new(false)));
    assert!(matches!(result, Err(CapabilityError::Unavailable)));
}

fn voice_store(database: &Database) -> crate::modules::personal_voice::infrastructure::VoiceStore {
    crate::modules::personal_voice::infrastructure::VoiceStore {
        path: database.path.clone(),
        key: "test-key-not-production".into(),
        max_profiles: 32,
    }
}

#[test]
fn legacy_voice_migrates_once_without_losing_the_embedding() {
    let database = Database::new();
    let _journal = database.open();
    let connection = rusqlite::Connection::open(&database.path).unwrap();
    connection
        .pragma_update(None, "key", "test-key-not-production")
        .unwrap();
    connection.execute_batch("CREATE TABLE personal_voice_profile(id INTEGER PRIMARY KEY CHECK(id=1),embedding TEXT NOT NULL)").unwrap();
    connection
        .execute(
            "INSERT INTO personal_voice_profile VALUES(1,?1)",
            [serde_json::to_string(&vec![0.25f32; 192]).unwrap()],
        )
        .unwrap();
    let store = voice_store(&database);
    let profiles = store.list().unwrap();
    assert_eq!(profiles.len(), 1);
    assert_eq!(profiles[0].name, "Voz anterior");
    assert!(profiles[0].is_default);
    assert_eq!(store.load().unwrap(), vec![0.25; 192]);
    let id = profiles[0].id.clone();
    assert_eq!(voice_store(&database).list().unwrap()[0].id, id);
    assert_eq!(
        connection
            .query_row("SELECT count(*) FROM personal_voice_profile", [], |r| r
                .get::<_, i64>(0))
            .unwrap(),
        0
    );
    store.delete(&id).unwrap();
    assert!(voice_store(&database).list().unwrap().is_empty());
    assert!(store.load().is_err());
}

#[test]
fn named_voices_preserve_default_and_block_destructive_changes_while_active() {
    let database = Database::new();
    let journal = database.open();
    let store = voice_store(&database);
    let first = uuid::Uuid::new_v4().to_string();
    let second = uuid::Uuid::new_v4().to_string();
    store
        .save_profile(&first, "Mi voz", &[0.1; 192], false)
        .unwrap();
    let sql_name = "Voz'; DROP TABLE operations; --";
    store
        .save_profile(&second, sql_name, &[0.2; 192], false)
        .unwrap();
    assert_eq!(
        store
            .list()
            .unwrap()
            .iter()
            .filter(|p| p.is_default)
            .count(),
        1
    );
    assert!(matches!(
        store.delete(&first),
        Err(Error::Audio(AudioErrorCode::ChooseAnotherDefaultVoice))
    ));
    let active = journal
        .accept(
            "named-capture",
            Command::StartVoiceProfileAudio {
                input_id: "hardware".into(),
                voice_profile_id: first.clone(),
            },
        )
        .unwrap();
    assert!(matches!(store.set_default(&second), Err(Error::Busy)));
    assert!(matches!(store.delete(&second), Err(Error::Busy)));
    assert!(matches!(
        journal.accept(
            "replace-during-capture",
            Command::EnrollVoiceProfile {
                input_id: "hardware".into(),
                profile_id: first.clone(),
                name: "Reemplazo".into(),
                replace: true
            }
        ),
        Err(Error::Busy)
    ));
    journal.cancel(&active.operation_id).unwrap();
    store.set_default(&second).unwrap();
    assert_eq!(voice_store(&database).list().unwrap()[0].id, second);
    assert_eq!(store.load().unwrap(), vec![0.2; 192]);
    assert!(
        store
            .save_profile(&first, "Invalid", &[f32::NAN; 192], true)
            .is_err()
    );
    assert_eq!(store.embedding(&first).unwrap(), vec![0.1; 192]);
    store
        .save_profile(&first, "Voz nueva", &[0.3; 192], true)
        .unwrap();
    assert_eq!(store.embedding(&first).unwrap(), vec![0.3; 192]);
    assert_eq!(store.list().unwrap().len(), 2);
    store.delete(&first).unwrap();
    store.delete(&first).unwrap();
    assert!(matches!(store.embedding(&first), Err(Error::NotFound)));
    assert_eq!(store.list().unwrap()[0].name, sql_name);
    store.delete(&second).unwrap();
    assert!(store.list().unwrap().is_empty());
}

#[test]
fn named_enrollment_is_validated_idempotent_and_never_resumes_after_restart() {
    let database = Database::new();
    let journal = database.open();
    let store = voice_store(&database);
    let id = uuid::Uuid::new_v4().to_string();
    let command = Command::EnrollVoiceProfile {
        input_id: "hardware".into(),
        profile_id: id.clone(),
        name: "Otra voz".into(),
        replace: false,
    };
    let first = journal.accept("named-enroll", command.clone()).unwrap();
    assert_eq!(
        journal
            .accept("named-enroll", command)
            .unwrap()
            .operation_id,
        first.operation_id
    );
    assert!(matches!(
        journal.accept(
            "bad-name",
            Command::EnrollVoiceProfile {
                input_id: "hardware".into(),
                profile_id: id.clone(),
                name: "\n".into(),
                replace: false
            }
        ),
        Err(Error::Invalid)
    ));
    journal.recover().unwrap();
    assert_eq!(
        journal.get(&first.operation_id).unwrap().status,
        Status::Interrupted
    );
    assert!(store.list().unwrap().is_empty());
    let limited = crate::modules::personal_voice::infrastructure::VoiceStore {
        max_profiles: 1,
        ..store
    };
    limited
        .save_profile(&id, "Primera", &[0.1; 192], false)
        .unwrap();
    assert!(matches!(
        limited.save_profile(
            &uuid::Uuid::new_v4().to_string(),
            "Segunda",
            &[0.2; 192],
            false
        ),
        Err(Error::Audio(AudioErrorCode::VoiceProfileCapacity))
    ));
    assert_eq!(limited.list().unwrap().len(), 1);
}

#[tokio::test]
async fn voice_http_uses_authentication_returns_only_metadata_and_guards_default_deletion() {
    let database = Database::new();
    let journal = database.open();
    let store = Arc::new(voice_store(&database));
    let first = uuid::Uuid::new_v4().to_string();
    let second = uuid::Uuid::new_v4().to_string();
    store
        .save_profile(&first, "Principal", &[0.1; 192], false)
        .unwrap();
    store
        .save_profile(&second, "Alternativa", &[0.2; 192], false)
        .unwrap();
    let app = router(Bff {
        operations: Operations::new(journal.clone()),
        token: "test-token".into(),
        api_version: crate::commons::protocol::default_api_version(),
        voices: store.clone(),
    });
    let unauthorized = app
        .clone()
        .oneshot(
            Request::builder()
                .uri("/v1/voice-profiles")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(unauthorized.status(), StatusCode::UNAUTHORIZED);
    let unauthorized_delete = app
        .clone()
        .oneshot(
            Request::builder()
                .method("DELETE")
                .uri(format!("/v1/voice-profiles/{first}"))
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(unauthorized_delete.status(), StatusCode::UNAUTHORIZED);
    assert_eq!(store.list().unwrap().len(), 2);

    let response = app
        .clone()
        .oneshot(
            request("GET", "/v1/voice-profiles")
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(response.status(), StatusCode::OK);
    let data =
        String::from_utf8(to_bytes(response.into_body(), 8192).await.unwrap().to_vec()).unwrap();
    assert!(!data.contains("embedding"));
    assert!(!data.contains("test-key"));
    assert_eq!(
        serde_json::from_str::<serde_json::Value>(&data)
            .unwrap()
            .as_array()
            .unwrap()
            .len(),
        2
    );
    let deletion = app
        .clone()
        .oneshot(
            request("DELETE", &format!("/v1/voice-profiles/{first}"))
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(deletion.status(), StatusCode::CONFLICT);
    let active = journal
        .accept(
            "voice-http-active",
            Command::StartVoiceProfileAudio {
                input_id: "hardware".into(),
                voice_profile_id: first.clone(),
            },
        )
        .unwrap();
    let busy = app
        .clone()
        .oneshot(
            request("POST", &format!("/v1/voice-profiles/{second}/default"))
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(busy.status(), StatusCode::CONFLICT);
    journal.cancel(&active.operation_id).unwrap();
    let changed = app
        .clone()
        .oneshot(
            request("POST", &format!("/v1/voice-profiles/{second}/default"))
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(changed.status(), StatusCode::NO_CONTENT);
    let deleted = app
        .oneshot(
            request("DELETE", &format!("/v1/voice-profiles/{first}"))
                .body(Body::empty())
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(deleted.status(), StatusCode::NO_CONTENT);
    assert!(matches!(store.embedding(&first), Err(Error::NotFound)));
}
