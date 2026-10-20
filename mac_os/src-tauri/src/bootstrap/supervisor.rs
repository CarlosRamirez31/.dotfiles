use super::launch::Launch;
use crate::commons::ConnectionInfo;
use std::{
    path::PathBuf,
    process::{Child, ChildStdin, Command, Stdio},
    sync::Mutex,
    time::Duration,
};

pub struct Supervisor {
    child: Mutex<Child>,
    pipe: Mutex<Option<ChildStdin>>,
    shutdown_seconds: u64,
    pub connection: ConnectionInfo,
    pub reconnect_ms: u64,
}
impl Drop for Supervisor {
    fn drop(&mut self) {
        self.stop();
    }
}
impl Supervisor {
    pub fn connection(&self) -> Result<ConnectionInfo, String> {
        let mut child = self.child.lock().map_err(|_| "service_unavailable")?;
        if child
            .try_wait()
            .map_err(|_| "service_unavailable")?
            .is_some()
        {
            return Err("service_stopped".into());
        }
        Ok(self.connection.clone())
    }
    pub fn stop(&self) {
        // Serialize repeated Exit/Drop calls, then let EOF request cooperative shutdown.
        let mut child = self.child.lock().unwrap_or_else(|error| error.into_inner());
        self.pipe
            .lock()
            .unwrap_or_else(|error| error.into_inner())
            .take();
        let deadline = std::time::Instant::now() + Duration::from_secs(self.shutdown_seconds);
        loop {
            match child.try_wait() {
                Ok(Some(_)) => return,
                Ok(None) if std::time::Instant::now() < deadline => {
                    std::thread::sleep(Duration::from_millis(25));
                }
                _ => break,
            }
        }
        tracing::warn!(event = "supervisor.forced_stop");
        let _ = child.kill();
        let _ = child.wait();
    }
    pub fn start(
        directory: PathBuf,
        voice_runtime: PathBuf,
        voice_script: PathBuf,
        options: crate::commons::options::Options,
    ) -> Result<Self, String> {
        let shutdown_seconds = options.shutdown_seconds;
        let reconnect_ms = options.reconnect_ms;
        let mut child =
            Command::new(std::env::current_exe().map_err(|_| "executable_unavailable")?)
                .arg(crate::commons::protocol::LOCAL_SERVICE_MODE)
                .stdin(Stdio::piped())
                .stdout(Stdio::piped())
                .stderr(Stdio::null())
                .spawn()
                .map_err(|_| "service_start_failed")?;
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
        let result = super::handshake::exchange(&mut child, &launch);
        match result {
            Ok((pipe, connection)) => Ok(Self {
                child: Mutex::new(child),
                pipe: Mutex::new(Some(pipe)),
                shutdown_seconds,
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

#[cfg(test)]
impl Supervisor {
    pub(crate) fn for_test(child: Child, pipe: Option<ChildStdin>, shutdown_seconds: u64) -> Self {
        Self {
            child: Mutex::new(child),
            pipe: Mutex::new(pipe),
            shutdown_seconds,
            connection: ConnectionInfo {
                endpoint: String::new(),
                token: String::new(),
                protocol_version: crate::commons::protocol::PROTOCOL_VERSION,
                api_version: crate::commons::protocol::default_api_version(),
            },
            reconnect_ms: 1500,
        }
    }
    pub(crate) fn exit_code_for_test(&self) -> Option<i32> {
        self.child
            .lock()
            .unwrap()
            .try_wait()
            .unwrap()
            .unwrap()
            .code()
    }
    pub(crate) fn exited_for_test(&self) -> bool {
        self.child.lock().unwrap().try_wait().unwrap().is_some()
    }
}
