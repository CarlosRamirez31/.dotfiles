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

#[test]
fn handshake_acl_rejects_wrong_peer_and_malformed_payload() {
    use crate::bootstrap::decode_connection;
    let valid = serde_json::json!({
        "endpoint": "http://127.0.0.1:12345", "token": "test-token",
        "protocolVersion": crate::commons::protocol::PROTOCOL_VERSION, "apiVersion": "v1",
        "providerPrivateData": "discard"
    });
    assert!(decode_connection(&valid.to_string(), "test-token").is_ok());
    assert!(matches!(
        decode_connection(&valid.to_string(), "other-token"),
        Err("service_protocol_mismatch")
    ));
    let mut remote = valid.clone();
    remote["endpoint"] = serde_json::json!("https://external.example");
    assert!(matches!(
        decode_connection(&remote.to_string(), "test-token"),
        Err("service_protocol_mismatch")
    ));
    let mut version = valid;
    version["protocolVersion"] = serde_json::json!(999);
    assert!(matches!(
        decode_connection(&version.to_string(), "test-token"),
        Err("service_protocol_mismatch")
    ));
    assert!(matches!(
        decode_connection("not-json", "test-token"),
        Err("service_start_failed")
    ));
}
