use super::worker_acl as acl;
use crate::{
    modules::audio::application::{PersonalVoice, cancelled},
    modules::audio::domain::capability::{CapabilityError as Error, CapabilityResult as Result},
};
use std::{
    io::{BufRead, BufReader, Read, Write},
    process::{Child, ChildStdin, Command, Stdio},
    sync::{
        Arc,
        atomic::AtomicBool,
        mpsc::{Receiver, sync_channel},
    },
    time::{Duration, Instant},
};

pub struct NomoWorker {
    child: Child,
    input: ChildStdin,
    replies: Receiver<String>,
    stop: Arc<AtomicBool>,
    options: crate::modules::personal_voice::options::VoiceOptions,
}
impl Drop for NomoWorker {
    fn drop(&mut self) {
        let _ = self.child.kill();
        let _ = self.child.wait();
    }
}
impl NomoWorker {
    pub fn start(
        root: &std::path::Path,
        script: &std::path::Path,
        stop: Arc<AtomicBool>,
        embedding: Option<&[f32]>,
        options: crate::modules::personal_voice::options::VoiceOptions,
    ) -> Result<Self> {
        if embedding.is_some_and(|v| v.len() != 192 || v.iter().any(|x| !x.is_finite())) {
            return Err(Error::InvalidInput);
        }
        if !root.join("venv/bin/python").is_file()
            || !root.join("eres/pretrained_eres2netv2.ckpt").is_file()
        {
            return Err(Error::Unavailable);
        }
        let mut child = Command::new(root.join("venv/bin/python"))
            .arg("-I")
            .arg(script)
            .arg(root)
            .arg(if embedding.is_some() {
                acl::STREAM_MODE
            } else {
                acl::ENROLL_MODE
            })
            .arg(std::process::id().to_string())
            .env("HF_HUB_OFFLINE", "1")
            .env("MODELSCOPE_OFFLINE", "1")
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::null())
            .spawn()
            .map_err(|_| Error::Unavailable)?;
        let input = child.stdin.take().ok_or(Error::InvalidResponse)?;
        let output = child.stdout.take().ok_or(Error::InvalidResponse)?;
        let (sender, replies) = sync_channel(1);
        std::thread::spawn(move || {
            let mut reader = BufReader::new(output);
            loop {
                let mut line = String::new();
                if reader.by_ref().take(16384).read_line(&mut line).is_err()
                    || line.is_empty()
                    || !line.ends_with('\n')
                {
                    break;
                }
                if sender.send(line).is_err() {
                    break;
                }
            }
        });
        let mut worker = Self {
            child,
            input,
            replies,
            stop,
            options,
        };
        let ready = worker.receive(Duration::from_secs(worker.options.load_seconds))?;
        acl::ready(&ready)?;
        if let Some(embedding) = embedding {
            worker.write_pcm(embedding)?;
        }
        Ok(worker)
    }
    fn receive(&self, timeout: Duration) -> Result<serde_json::Value> {
        let until = Instant::now() + timeout;
        loop {
            if cancelled(&self.stop) {
                return Err(Error::Cancelled);
            }
            match self.replies.recv_timeout(Duration::from_millis(25)) {
                Ok(line) => {
                    return acl::response(&line);
                }
                Err(std::sync::mpsc::RecvTimeoutError::Disconnected) => {
                    return Err(Error::Unavailable);
                }
                Err(_) if Instant::now() >= until => {
                    return Err(Error::Timeout);
                }
                Err(_) => {}
            }
        }
    }
    fn write_pcm(&mut self, pcm: &[f32]) -> Result<()> {
        let mut bytes = Vec::with_capacity(pcm.len() * 4);
        for sample in pcm {
            bytes.extend_from_slice(&sample.to_le_bytes());
        }
        self.input
            .write_all(&bytes)
            .map_err(|_| Error::Unavailable)?;
        self.input.flush().map_err(|_| Error::Unavailable)
    }
    fn request(&mut self, pcm: &[f32], timeout: Duration) -> Result<serde_json::Value> {
        self.input
            .write_all(&(pcm.len() as u32).to_le_bytes())
            .map_err(|_| Error::Unavailable)?;
        self.write_pcm(pcm)?;
        self.receive(timeout)
    }
}
impl crate::modules::personal_voice::application::EnrollmentSession for NomoWorker {
    fn enroll(&mut self, pcm: &[f32]) -> Result<Vec<f32>> {
        if pcm.len() != 160000 || pcm.iter().any(|v| !v.is_finite()) {
            return Err(Error::InvalidInput);
        }
        let reply = self.request(pcm, Duration::from_secs(self.options.enroll_seconds))?;
        acl::embedding(reply)
    }
}
impl PersonalVoice for NomoWorker {
    fn probability(&mut self, pcm: &[f32]) -> Result<f32> {
        if pcm.len() != 2560 || pcm.iter().any(|v| !v.is_finite()) {
            return Err(Error::InvalidInput);
        }
        let reply = self.request(pcm, Duration::from_secs(self.options.inference_seconds))?;
        acl::probability(reply)
    }
}
