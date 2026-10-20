use crate::commons::ConnectionInfo;
use serde::{Deserialize, Serialize};
use std::{
    io::{BufRead, BufReader, Write},
    path::PathBuf,
    process::{Child, ChildStdin, Command, Stdio},
    sync::Mutex,
    time::Duration,
};

#[derive(Serialize, Deserialize)]
struct Launch {
    options: crate::commons::options::Options,
    directory: PathBuf,
    token: String,
    voice_runtime: PathBuf,
    voice_script: PathBuf,
}

pub struct Supervisor {
    child: Mutex<Child>,
    _pipe: ChildStdin,
    pub connection: ConnectionInfo,
    pub reconnect_ms: u64,
}
impl Drop for Supervisor {
    fn drop(&mut self) {
        tracing::info!(event = "supervisor.stopping");
        if let Ok(child) = self.child.get_mut() {
            let _ = child.kill();
            let _ = child.wait();
        }
    }
}
impl Supervisor {
    pub fn start(
        directory: PathBuf,
        voice_runtime: PathBuf,
        voice_script: PathBuf,
        options: crate::commons::options::Options,
    ) -> Result<Self, String> {
        let startup_seconds = options.startup_seconds;
        let reconnect_ms = options.reconnect_ms;
        let mut child =
            Command::new(std::env::current_exe().map_err(|_| "executable_unavailable")?)
                .arg("--local-service")
                .stdin(Stdio::piped())
                .stdout(Stdio::piped())
                .stderr(Stdio::null())
                .spawn()
                .map_err(|_| "service_start_failed")?;
        let result = (|| {
            let mut pipe = child.stdin.take().ok_or("service_pipe_unavailable")?;
            let token = format!(
                "{}{}",
                uuid::Uuid::new_v4().simple(),
                uuid::Uuid::new_v4().simple()
            );
            let launch = Launch {
                options,
                directory,
                voice_runtime,
                voice_script,
                token: token.clone(),
            };
            serde_json::to_writer(&mut pipe, &launch).map_err(|_| "service_handshake_failed")?;
            writeln!(pipe).map_err(|_| "service_handshake_failed")?;
            pipe.flush().map_err(|_| "service_handshake_failed")?;
            let stdout = child.stdout.take().ok_or("service_pipe_unavailable")?;
            let (sender, receiver) = std::sync::mpsc::sync_channel(1);
            std::thread::spawn(move || {
                let mut ready = String::new();
                let result = BufReader::new(stdout).read_line(&mut ready).map(|_| ready);
                let _ = sender.send(result);
            });
            let ready = receiver
                .recv_timeout(Duration::from_secs(startup_seconds))
                .map_err(|_| "service_start_timeout")?
                .map_err(|_| "service_handshake_failed")?;
            let connection: ConnectionInfo =
                serde_json::from_str(&ready).map_err(|_| "service_start_failed")?;
            if connection.token != token
                || connection.protocol_version != 1
                || !connection.endpoint.starts_with("http://127.0.0.1:")
            {
                return Err("service_protocol_mismatch");
            }
            Ok((pipe, connection))
        })();
        match result {
            Ok((pipe, connection)) => Ok(Self {
                child: Mutex::new(child),
                _pipe: pipe,
                connection,
                reconnect_ms,
            }),
            Err(error) => {
                let _ = child.kill();
                let _ = child.wait();
                Err(error.into())
            }
        }
    }
}

#[tauri::command]
pub fn local_connection(state: tauri::State<'_, Supervisor>) -> Result<ConnectionInfo, String> {
    let mut child = state.child.lock().map_err(|_| "service_unavailable")?;
    if child
        .try_wait()
        .map_err(|_| "service_unavailable")?
        .is_some()
    {
        return Err("service_stopped".into());
    }
    Ok(state.connection.clone())
}

#[cfg(target_os = "macos")]
fn database_key(existing: bool) -> Result<String, Box<dyn std::error::Error>> {
    use security_framework::passwords::{get_generic_password, set_generic_password};
    let service = "com.dotfiles.microphone.local.sqlcipher";
    let account = "database-v1";
    match get_generic_password(service, account) {
        Ok(key) => Ok(String::from_utf8(key)?),
        Err(error) if error.code() == -25300 && !existing => {
            let key = format!(
                "{}{}",
                uuid::Uuid::new_v4().simple(),
                uuid::Uuid::new_v4().simple()
            );
            set_generic_password(service, account, key.as_bytes())?;
            Ok(key)
        }
        Err(error) => Err(Box::new(error)),
    }
}
#[cfg(not(target_os = "macos"))]
fn database_key(_: bool) -> Result<String, Box<dyn std::error::Error>> {
    Err("Local service currently supports macOS only".into())
}

pub fn service() -> Result<(), Box<dyn std::error::Error>> {
    use crate::modules::{
        diagnostics::infrastructure::SqlCipherCheck,
        operations::{
            application::Operations,
            infrastructure::SqlCipherJournal,
            presentation::{Bff, router},
        },
    };
    use std::sync::Arc;
    let mut input = BufReader::new(std::io::stdin());
    let mut line = String::new();
    input.read_line(&mut line)?;
    let launch: Launch = serde_json::from_str(&line)?;
    launch.options.validate()?;
    std::fs::create_dir_all(&launch.directory)?;
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        std::fs::set_permissions(&launch.directory, std::fs::Permissions::from_mode(0o700))?;
    }
    let lock = std::fs::OpenOptions::new()
        .create(true)
        .truncate(false)
        .write(true)
        .open(launch.directory.join("service.lock"))?;
    lock.try_lock()?;
    let _logs = crate::commons::logging::initialize(
        &launch.directory.join("logs"),
        "service",
        &launch.options.logging,
    )?;
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
    let handler = Arc::new(LocalHandler {
        checker,
        voice: crate::modules::personal_voice::infrastructure::VoiceStore { path, key },
        runtime: launch.voice_runtime,
        script: launch.voice_script,
        options: launch.options.voice,
    });
    let operations = Operations::new(Arc::new(journal));
    let (shutdown_tx, shutdown_rx) = tokio::sync::oneshot::channel();
    std::thread::spawn(move || {
        // Parent keeps stdin open for its lifetime. EOF also handles an abrupt host exit.
        let mut sink = std::io::sink();
        let _ = std::io::copy(&mut input, &mut sink);
        let _ = shutdown_tx.send(());
    });
    tokio::runtime::Builder::new_multi_thread().enable_all().build()?.block_on(async move {
        let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await?;
        let info = ConnectionInfo { endpoint: format!("http://{}", listener.local_addr()?), token: launch.token.clone(), protocol_version: 1 };
        let app = router(Bff { operations: operations.clone(), token: launch.token });
        tracing::info!(event = "service.ready", protocol_version = 1);
        serde_json::to_writer(std::io::stdout(), &info)?;
        println!();
        std::io::stdout().flush()?;
        tokio::select! {
            _ = shutdown_rx => { tracing::info!(event = "service.parent_disconnected"); operations.shutdown(); },
            result = operations.clone().run(handler) => { result.map_err(|_| "operation_worker_failed")?; },
            result = axum::serve(listener, app) => { result?; },
        }
        tracing::info!(event = "service.stopped");
        drop(lock);
        Ok::<(), Box<dyn std::error::Error>>(())
    })
}

struct LocalHandler {
    checker: crate::modules::diagnostics::infrastructure::SqlCipherCheck,
    voice: crate::modules::personal_voice::infrastructure::VoiceStore,
    runtime: PathBuf,
    script: PathBuf,
    options: crate::modules::personal_voice::options::VoiceOptions,
}
impl crate::modules::operations::application::CommandHandler for LocalHandler {
    fn execute(
        &self,
        command: crate::commons::Command,
        cancelled: std::sync::Arc<std::sync::atomic::AtomicBool>,
        progress: &dyn Fn(&str) -> crate::commons::Result<()>,
    ) -> crate::commons::Result<crate::modules::operations::application::Completion> {
        use crate::modules::{
            audio::infrastructure, operations::application::StorageCheck,
            personal_voice::infrastructure::NomoWorker,
        };
        match command {
            crate::commons::Command::CheckStorage => self.checker.check().map(Into::into),
            crate::commons::Command::EnrollVoice { input_id } => {
                progress("preparing_voice_model")?;
                let mut worker = NomoWorker::start(
                    &self.runtime,
                    &self.script,
                    cancelled.clone(),
                    None,
                    self.options.clone(),
                )?;
                progress("recording_enrollment_10_seconds")?;
                let pcm = infrastructure::enroll(&input_id, cancelled.clone())?;
                progress("creating_voice_profile")?;
                let embedding = worker.enroll(&pcm)?;
                if cancelled.load(std::sync::atomic::Ordering::Acquire) {
                    return Err(crate::commons::Error::Audio("enrollment_cancelled"));
                }
                self.voice.save(&embedding)?;
                Ok(crate::modules::operations::application::Completion {
                    detail: "voice_enrolled".into(),
                    effect_committed: true,
                })
            }
            crate::commons::Command::StartAudio {
                input_id,
                personal_voice,
            } => {
                let voice = if personal_voice {
                    progress("preparing_voice_model")?;
                    let embedding = self.voice.load()?;
                    Some(Box::new(NomoWorker::start(
                        &self.runtime,
                        &self.script,
                        cancelled.clone(),
                        Some(&embedding),
                        self.options.clone(),
                    )?)
                        as Box<dyn crate::modules::audio::application::PersonalVoice>)
                } else {
                    None
                };
                infrastructure::run(
                    &input_id,
                    cancelled,
                    voice,
                    Box::new(crate::modules::ai_rnnoise::infrastructure::RnNoise::default()),
                    progress,
                    self.options.threshold,
                )
                .map(Into::into)
            }
        }
    }
}

#[tauri::command]
pub fn public_options(
    state: tauri::State<'_, Supervisor>,
) -> crate::commons::options::ClientOptions {
    crate::commons::options::ClientOptions {
        reconnect_ms: state.reconnect_ms,
    }
}
