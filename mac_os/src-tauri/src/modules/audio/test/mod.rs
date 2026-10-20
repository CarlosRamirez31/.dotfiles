#[test]
fn downsample_preserves_block_continuity_and_suppresses_aliasing() {
    use crate::modules::audio::domain::Downsample;
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

#[tokio::test]
async fn device_http_uses_injected_catalog_and_preserves_errors() {
    use crate::commons::{AudioErrorCode, Error, Result};
    use crate::modules::audio::{
        application::{DeviceCatalog, DeviceService},
        domain::{Devices, Input},
    };
    use crate::modules::operations::{
        application::Operations,
        presentation::{Bff, router},
    };
    use crate::modules::personal_voice::infrastructure::VoiceStore;
    use crate::tests::support::Database;
    use axum::{
        body::{Body, to_bytes},
        http::{Request, StatusCode},
    };
    use std::sync::{
        Arc,
        atomic::{AtomicUsize, Ordering},
    };
    use tower::ServiceExt;

    struct Catalog {
        fail: bool,
        calls: Arc<AtomicUsize>,
    }
    impl DeviceCatalog for Catalog {
        fn list(&self) -> Result<Devices> {
            self.calls.fetch_add(1, Ordering::SeqCst);
            if self.fail {
                return Err(Error::Audio(AudioErrorCode::AudioDeviceOrFormatUnavailable));
            }
            Ok(Devices {
                inputs: vec![Input {
                    id: "controlled-input".into(),
                    name: "Test microphone".into(),
                }],
                blackhole_available: true,
            })
        }
    }
    for fail in [false, true] {
        let database = Database::new();
        let calls = Arc::new(AtomicUsize::new(0));
        let app = router(Bff {
            operations: Operations::new(database.open()),
            token: "test-token".into(),
            api_version: crate::commons::protocol::default_api_version(),
            voices: Arc::new(VoiceStore {
                path: database.path.clone(),
                key: "test-key-not-production".into(),
                max_profiles: 32,
            }),
            devices: DeviceService::new(Arc::new(Catalog {
                fail,
                calls: calls.clone(),
            })),
        });
        let unauthorized = app
            .clone()
            .oneshot(
                Request::builder()
                    .uri("/v1/audio/devices")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(unauthorized.status(), StatusCode::UNAUTHORIZED);
        assert_eq!(calls.load(Ordering::SeqCst), 0);
        let response = app
            .oneshot(
                Request::builder()
                    .uri("/v1/audio/devices")
                    .header("Authorization", "Bearer test-token")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        let status = response.status();
        let payload: serde_json::Value =
            serde_json::from_slice(&to_bytes(response.into_body(), 4096).await.unwrap()).unwrap();
        assert_eq!(calls.load(Ordering::SeqCst), 1);
        if fail {
            assert_eq!(status, StatusCode::CONFLICT);
            assert_eq!(
                payload["error"],
                AudioErrorCode::AudioDeviceOrFormatUnavailable.as_str()
            );
        } else {
            assert_eq!(status, StatusCode::OK);
            assert_eq!(payload["inputs"][0]["id"], "controlled-input");
            assert_eq!(payload["blackholeAvailable"], true);
        }
    }
}

mod pipeline;
