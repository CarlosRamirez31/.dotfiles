use crate::{
    commons::{Error, Result},
    modules::audio::application::{PersonalVoice, cancelled},
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
    ) -> Result<Self> {
        if !root.join("venv/bin/python").is_file()
            || !root.join("eres/pretrained_eres2netv2.ckpt").is_file()
        {
            return Err(Error::Audio("personal_voice_runtime_not_installed"));
        }
        let mut child = Command::new(root.join("venv/bin/python"))
            .arg("-I")
            .arg(script)
            .arg(root)
            .arg(if embedding.is_some() {
                "stream"
            } else {
                "enroll"
            })
            .env("HF_HUB_OFFLINE", "1")
            .env("MODELSCOPE_OFFLINE", "1")
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::null())
            .spawn()
            .map_err(|_| Error::Audio("personal_voice_worker_failed"))?;
        let input = child.stdin.take().ok_or(Error::Storage)?;
        let output = child.stdout.take().ok_or(Error::Storage)?;
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
        };
        let ready = worker.receive(Duration::from_secs(120))?;
        if ready.get("ready").and_then(|v| v.as_bool()) != Some(true)
            || ready.get("protocol").and_then(|v| v.as_i64()) != Some(1)
        {
            return Err(Error::Audio("personal_voice_model_load_failed"));
        }
        if let Some(embedding) = embedding {
            worker.write_pcm(embedding)?;
        }
        Ok(worker)
    }
    fn receive(&self, timeout: Duration) -> Result<serde_json::Value> {
        let until = Instant::now() + timeout;
        loop {
            if cancelled(&self.stop) {
                return Err(Error::Audio("personal_voice_cancelled"));
            }
            match self.replies.recv_timeout(Duration::from_millis(25)) {
                Ok(line) => {
                    let result: serde_json::Value = serde_json::from_str(&line)
                        .map_err(|_| Error::Audio("personal_voice_invalid_response"))?;
                    if result.get("error").is_some() {
                        return Err(Error::Audio("personal_voice_inference_failed"));
                    }
                    return Ok(result);
                }
                Err(std::sync::mpsc::RecvTimeoutError::Disconnected) => {
                    return Err(Error::Audio("personal_voice_worker_stopped"));
                }
                Err(_) if Instant::now() >= until => {
                    return Err(Error::Audio("personal_voice_timeout"));
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
            .map_err(|_| Error::Audio("personal_voice_worker_stopped"))?;
        self.input
            .flush()
            .map_err(|_| Error::Audio("personal_voice_worker_stopped"))
    }
    fn request(&mut self, pcm: &[f32], timeout: Duration) -> Result<serde_json::Value> {
        self.input
            .write_all(&(pcm.len() as u32).to_le_bytes())
            .map_err(|_| Error::Audio("personal_voice_worker_stopped"))?;
        self.write_pcm(pcm)?;
        self.receive(timeout)
    }
    pub fn enroll(&mut self, pcm: &[f32]) -> Result<Vec<f32>> {
        let reply = self.request(pcm, Duration::from_secs(60))?;
        serde_json::from_value(reply.get("embedding").cloned().ok_or(Error::Storage)?)
            .map_err(|_| Error::Storage)
    }
}
impl PersonalVoice for NomoWorker {
    fn probability(&mut self, pcm: &[f32]) -> Result<f32> {
        let reply = self.request(pcm, Duration::from_secs(2))?;
        let probability = reply
            .get("probability")
            .and_then(|v| v.as_f64())
            .ok_or(Error::Audio("personal_voice_invalid_response"))?
            as f32;
        if !probability.is_finite() || !(0.0..=1.0).contains(&probability) {
            return Err(Error::Audio("personal_voice_invalid_probability"));
        }
        Ok(probability)
    }
}
