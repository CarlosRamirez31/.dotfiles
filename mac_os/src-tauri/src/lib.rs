mod bootstrap;
mod commons;
mod modules;

pub fn run() {
    if std::env::args().any(|argument| argument == "--local-service") {
        if bootstrap::service().is_err() {
            std::process::exit(1);
        }
        return;
    }
    use tauri::Manager;
    tauri::Builder::default()
        .setup(|app| {
            let directory = app.path().app_data_dir()?.join("local-service");
            let options = commons::options::Options::load().map_err(std::io::Error::other)?;
            let logs =
                commons::logging::initialize(&directory.join("logs"), "host", &options.logging)?;
            app.manage(logs);
            let (runtime, script) = if cfg!(debug_assertions) {
                let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR"))
                    .parent()
                    .unwrap();
                (
                    root.join(".runtime/personal-voice"),
                    root.join("runtime/personal-voice/worker.py"),
                )
            } else {
                (
                    directory.join("runtime/personal-voice"),
                    app.path().resource_dir()?.join("personal-voice/worker.py"),
                )
            };
            let runtime = options.voice.runtime.clone().unwrap_or(runtime);
            let supervisor = bootstrap::Supervisor::start(directory, runtime, script, options)
                .map_err(std::io::Error::other)?;
            app.manage(supervisor);
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            bootstrap::local_connection,
            bootstrap::public_options,
            commons::logging::client_log
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

#[cfg(test)]
#[path = "../../test/rust.rs"]
mod tests;
