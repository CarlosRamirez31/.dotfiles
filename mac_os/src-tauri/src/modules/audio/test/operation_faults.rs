use crate::commons::{AudioErrorCode, Command, Error};
use crate::modules::operations::{application::Journal, domain::Status};
use crate::tests::support::Database;

#[test]
fn controlled_audio_failures_are_persisted_and_allow_a_new_session() {
    let database = Database::new();
    let journal = database.open();
    for code in [
        AudioErrorCode::RequiresFloat3248khzMonoOrStereo,
        AudioErrorCode::AudioOverrunOrDeviceLost,
        AudioErrorCode::BlackholeOutputFailed,
    ] {
        let operation = journal
            .accept(
                &uuid::Uuid::new_v4().to_string(),
                Command::StartAudio {
                    input_id: "controlled-test-input".into(),
                    personal_voice: false,
                },
            )
            .unwrap();
        let claimed = journal.claim().unwrap().unwrap();
        assert_eq!(claimed.operation_id, operation.operation_id);
        journal
            .finish(&operation.operation_id, Err(Error::Audio(code)))
            .unwrap();
        let saved = journal.get(&operation.operation_id).unwrap();
        assert_eq!(saved.status, Status::Failed);
        assert_eq!(saved.detail.as_deref(), Some(code.as_str()));
        let events = journal.events(0).unwrap();
        assert!(
            events
                .iter()
                .any(|event| event.operation_id == operation.operation_id
                    && event.operation.status == Status::Failed)
        );
    }
    drop(journal);
    let reopened = database.open();
    reopened.recover().unwrap();
    assert!(reopened.claim().unwrap().is_none());
}
