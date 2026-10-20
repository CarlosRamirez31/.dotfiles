use super::{keychain::database_key, launch::Launch};
use crate::application::LocalHandler;
use crate::modules::{
    audio::{application::DeviceService, infrastructure::CoreAudioDeviceCatalog},
    diagnostics::infrastructure::SqlCipherCheck,
    operations::{
        application::{CommandHandler, Operations},
        infrastructure::SqlCipherJournal,
    },
    personal_voice::application::VoiceProfiles,
};
use std::sync::Arc;
pub(super) struct Services {
    pub operations: Operations,
    pub handler: Arc<dyn CommandHandler>,
    pub voices: Arc<dyn VoiceProfiles>,
    pub devices: DeviceService,
}
pub(super) fn compose(launch: &Launch) -> Result<Services, Box<dyn std::error::Error>> {
    let path = launch.directory.join("local.db");
    let key = database_key(path.exists()).inspect_err(|_| {
        tracing::error!(
            event = "service.start_failed",
            code = "keychain_unavailable"
        );
    })?;
    let journal = SqlCipherJournal::configured(&path, &key, launch.options.operations.clone())
        .map_err(|_| {
            tracing::error!(
                event = "service.start_failed",
                code = "encrypted_database_unavailable"
            );
            "encrypted_database_unavailable"
        })?;
    let checker = SqlCipherCheck {
        path: path.clone(),
        key: key.clone(),
    };
    let voice_factory = Arc::new(
        crate::modules::personal_voice::infrastructure::NomoFactory::new(
            launch.voice_runtime.clone(),
            launch.voice_script.clone(),
            launch.options.voice.clone(),
        ),
    );
    let voices: Arc<dyn crate::modules::personal_voice::application::VoiceProfiles> =
        Arc::new(crate::modules::personal_voice::infrastructure::VoiceStore {
            path,
            key,
            max_profiles: launch.options.voice.max_profiles,
        });
    let audio = Arc::new(crate::modules::audio::infrastructure::CoreAudioRuntime);
    let handler: Arc<dyn crate::modules::operations::application::CommandHandler> =
        Arc::new(LocalHandler {
            checker: Arc::new(checker),
            registration: crate::modules::personal_voice::application::VoiceRegistration {
                profiles: voices.clone(),
                factory: voice_factory.clone(),
                capture: audio.clone(),
            },
            sessions: crate::modules::audio::application::AudioSessions {
                profiles: voices.clone(),
                personal: voice_factory,
                playback: audio,
                noise: Arc::new(crate::modules::ai_rnnoise::infrastructure::RnNoiseFactory),
                voice_threshold: launch.options.voice.threshold,
            },
        });
    let operations = Operations::new(Arc::new(journal));
    Ok(Services {
        operations,
        handler,
        voices,
        devices: DeviceService::new(Arc::new(CoreAudioDeviceCatalog)),
    })
}
