use super::{launch::Launch, shutdown::drain_worker};
use crate::{
    commons::ConnectionInfo,
    modules::operations::presentation::{Bff, router},
};
use std::{
    io::{BufRead, BufReader, Write},
    time::Duration,
};

pub fn service() -> Result<(), Box<dyn std::error::Error>> {
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
    let super::composition::Services {
        operations,
        handler,
        voices,
        devices,
    } = super::composition::compose(&launch)?;
    let (shutdown_tx, shutdown_rx) = tokio::sync::oneshot::channel();
    std::thread::spawn(move || {
        // Parent keeps stdin open for its lifetime. EOF also handles an abrupt host exit.
        let mut sink = std::io::sink();
        let _ = std::io::copy(&mut input, &mut sink);
        let _ = shutdown_tx.send(());
    });
    let runtime = tokio::runtime::Builder::new_multi_thread()
        .enable_all()
        .build()?;
    let grace = Duration::from_secs(launch.options.shutdown_seconds);
    let result = runtime.block_on(async move {
        let listener = tokio::net::TcpListener::bind("127.0.0.1:0").await?;
        let info = ConnectionInfo {
            endpoint: format!("http://{}", listener.local_addr()?),
            token: launch.token.clone(),
            protocol_version: crate::commons::protocol::PROTOCOL_VERSION,
            api_version: launch.options.api_version.clone(),
        };
        let app = router(Bff {
            devices,
            operations: operations.clone(),
            token: launch.token,
            voices,
            api_version: launch.options.api_version.clone(),
        });
        tracing::info!(event = "service.ready", protocol_version = 1);
        serde_json::to_writer(std::io::stdout(), &info)?;
        println!();
        std::io::stdout().flush()?;
        let worker = operations.clone().run(handler);
        tokio::pin!(worker);
        let result = tokio::select! {
            _ = shutdown_rx => {
                tracing::info!(event = "service.parent_disconnected");
                operations.shutdown();
                drain_worker(worker, grace).await
            },
            result = &mut worker => result.map_err(|_| "operation_worker_failed".into()),
            result = axum::serve(listener, app) => {
                operations.shutdown();
                let drained = drain_worker(worker, grace).await;
                result.map_err(Box::<dyn std::error::Error>::from).and(drained)
            },
        };
        operations.shutdown();
        result?;
        tracing::info!(event = "service.stopped");
        Ok::<(), Box<dyn std::error::Error>>(())
    });
    // A blocked provider must not keep the service alive after its owner disappears.
    // On timeout the service exits; persisted unfinished work is recovered on next launch.
    runtime.shutdown_timeout(Duration::ZERO);
    result
}
