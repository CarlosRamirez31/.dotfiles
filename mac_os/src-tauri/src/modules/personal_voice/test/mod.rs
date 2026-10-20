use crate::tests::support::*;
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
