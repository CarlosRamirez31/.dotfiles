use super::voice_store;
use crate::commons::{AudioErrorCode, Error, Result};
use crate::modules::{
    audio::{
        application::AudioCapture,
        domain::capability::{CapabilityError, CapabilityResult},
    },
    personal_voice::application::{
        EnrollmentFactory, EnrollmentSession, RegistrationTarget, VoiceProfiles, VoiceRegistration,
    },
};
use crate::tests::support::Database;
use std::sync::{
    Arc,
    atomic::{AtomicBool, AtomicUsize, Ordering},
};

struct Capture(Arc<AtomicUsize>);
impl AudioCapture for Capture {
    fn enroll(&self, _: &str, _: Arc<AtomicBool>) -> Result<Vec<f32>> {
        assert_eq!(
            self.0.fetch_add(1, Ordering::SeqCst),
            1,
            "model must be prepared before capture"
        );
        Ok(vec![0.0; 160])
    }
}
struct Factory {
    steps: Arc<AtomicUsize>,
    fail: bool,
    cancel_after_inference: bool,
}
struct Session {
    cancelled: Arc<AtomicBool>,
    cancel_after_inference: bool,
}
impl EnrollmentFactory for Factory {
    fn prepare_enrollment(
        &self,
        cancelled: Arc<AtomicBool>,
    ) -> CapabilityResult<Box<dyn EnrollmentSession>> {
        self.steps.fetch_add(1, Ordering::SeqCst);
        if self.fail {
            return Err(CapabilityError::Unavailable);
        }
        Ok(Box::new(Session {
            cancelled,
            cancel_after_inference: self.cancel_after_inference,
        }))
    }
}
impl EnrollmentSession for Session {
    fn enroll(&mut self, _: &[f32]) -> CapabilityResult<Vec<f32>> {
        if self.cancel_after_inference {
            self.cancelled.store(true, Ordering::Release);
        }
        Ok(vec![0.25; 192])
    }
}

#[test]
fn registration_uses_ports_and_preserves_previous_voice_on_cancel_or_prepare_failure() {
    for (fail, cancel) in [(true, false), (false, true), (false, false)] {
        let database = Database::new();
        let _journal = database.open();
        let profiles = Arc::new(voice_store(&database));
        let id = uuid::Uuid::new_v4().to_string();
        profiles
            .save_profile(&id, "Previous voice", &[0.125; 192], false)
            .unwrap();
        let steps = Arc::new(AtomicUsize::new(0));
        let registration = VoiceRegistration {
            profiles: profiles.clone(),
            factory: Arc::new(Factory {
                steps: steps.clone(),
                fail,
                cancel_after_inference: cancel,
            }),
            capture: Arc::new(Capture(steps.clone())),
        };
        let result = registration.execute(
            "test-input",
            RegistrationTarget::Named {
                id: id.clone(),
                name: "Updated voice".into(),
                replace: true,
            },
            Arc::new(AtomicBool::new(false)),
            &|_| Ok(()),
        );
        if fail {
            assert!(matches!(
                result,
                Err(Error::Audio(
                    AudioErrorCode::PersonalVoiceRuntimeNotInstalled
                ))
            ));
            assert_eq!(steps.load(Ordering::SeqCst), 1);
        } else if cancel {
            assert!(matches!(
                result,
                Err(Error::Audio(AudioErrorCode::EnrollmentCancelled))
            ));
            assert_eq!(steps.load(Ordering::SeqCst), 2);
        } else {
            assert!(result.unwrap().effect_committed);
            assert_eq!(profiles.embedding(&id).unwrap(), vec![0.25; 192]);
            continue;
        }
        assert_eq!(profiles.embedding(&id).unwrap(), vec![0.125; 192]);
        assert_eq!(profiles.list().unwrap()[0].name, "Previous voice");
    }
}
