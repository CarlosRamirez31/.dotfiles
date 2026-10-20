use super::launch::Launch;
use crate::commons::ConnectionInfo;
use std::{
    io::{BufRead, BufReader, Write},
    process::{Child, ChildStdin},
    time::Duration,
};

pub(super) fn exchange(
    child: &mut Child,
    launch: &Launch,
) -> Result<(ChildStdin, ConnectionInfo), &'static str> {
    let mut pipe = child.stdin.take().ok_or("service_pipe_unavailable")?;
    serde_json::to_writer(&mut pipe, launch).map_err(|_| "service_handshake_failed")?;
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
        .recv_timeout(Duration::from_secs(launch.options.startup_seconds))
        .map_err(|_| "service_start_timeout")?
        .map_err(|_| "service_handshake_failed")?;
    let connection = decode_connection(&ready, &launch.token)?;
    Ok((pipe, connection))
}

pub(crate) fn decode_connection(
    ready: &str,
    expected_token: &str,
) -> Result<ConnectionInfo, &'static str> {
    let connection: ConnectionInfo =
        serde_json::from_str(ready).map_err(|_| "service_start_failed")?;
    if connection.token != expected_token
        || connection.protocol_version != crate::commons::protocol::PROTOCOL_VERSION
        || !local_endpoint(&connection.endpoint)
        || !crate::commons::protocol::valid_api_version(&connection.api_version)
    {
        return Err("service_protocol_mismatch");
    }
    Ok(connection)
}

fn local_endpoint(endpoint: &str) -> bool {
    let Some(authority) = endpoint.strip_prefix(LOCAL_HTTP_PREFIX) else {
        return false;
    };
    let Ok(address) = authority.parse::<std::net::SocketAddrV4>() else {
        return false;
    };
    address.ip() == &std::net::Ipv4Addr::LOCALHOST && address.port() != 0
}
const LOCAL_HTTP_PREFIX: &str = "http://";
