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
    use crate::modules::{
        audio::application::PersonalVoice, personal_voice::infrastructure::NomoWorker,
    };
    let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap();
    let runtime = root.join(".runtime/personal-voice");
    let script = root.join("runtime/personal-voice/worker.py");
    let stop = Arc::new(std::sync::atomic::AtomicBool::new(false));
    let mut enrollment =
        NomoWorker::start(&runtime, &script, stop.clone(), None, Default::default()).unwrap();
    let pcm: Vec<f32> = (0..160_000)
        .map(|i| 0.05 * (i as f32 * 440.0 * 2.0 * std::f32::consts::PI / 16_000.0).sin())
        .collect();
    let embedding = enrollment.enroll(&pcm).unwrap();
    assert_eq!(embedding.len(), 192);
    drop(enrollment);
    let mut worker = NomoWorker::start(
        &runtime,
        &script,
        stop,
        Some(&embedding),
        Default::default(),
    )
    .unwrap();
    let probability = worker.probability(&pcm[..2560]).unwrap();
    assert!((0.0..=1.0).contains(&probability));
}
