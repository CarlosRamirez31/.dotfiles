use crate::bootstrap::Supervisor;
use std::{
    process::{Command, Stdio},
    time::{Duration, Instant},
};

fn child_supervisor(script: &str) -> Supervisor {
    let mut child = Command::new("/bin/sh")
        .args(["-c", script])
        .stdin(Stdio::piped())
        .stdout(Stdio::null())
        .stderr(Stdio::null())
        .spawn()
        .unwrap();
    let pipe = child.stdin.take();
    Supervisor::for_test(child, pipe, 1)
}

#[test]
fn supervisor_closes_pipe_and_waits_for_graceful_exit() {
    let supervisor = child_supervisor("read value; exit 42");
    supervisor.stop();
    supervisor.stop();
    assert_eq!(supervisor.exit_code_for_test(), Some(42));
}

#[test]
fn supervisor_bounds_shutdown_of_an_unresponsive_child() {
    let supervisor = child_supervisor("exec sleep 30");
    let started = Instant::now();
    supervisor.stop();
    assert!(started.elapsed() < Duration::from_secs(3));
    assert!(supervisor.exited_for_test());
}

#[tokio::test]
async fn service_drain_has_a_deadline_without_a_living_host() {
    let result = crate::bootstrap::drain_worker(
        std::future::pending::<crate::commons::Result<()>>(),
        Duration::from_millis(25),
    )
    .await;
    assert_eq!(result.unwrap_err().to_string(), "service_shutdown_timeout");
}
