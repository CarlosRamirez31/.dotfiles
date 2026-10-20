use std::time::Duration;

pub(crate) async fn drain_worker(
    worker: impl std::future::Future<Output = crate::commons::Result<()>>,
    grace: Duration,
) -> Result<(), Box<dyn std::error::Error>> {
    match tokio::time::timeout(grace, worker).await {
        Ok(result) => result.map_err(|_| "operation_worker_failed".into()),
        Err(_) => {
            tracing::error!(event = "service.shutdown_timeout");
            Err("service_shutdown_timeout".into())
        }
    }
}
