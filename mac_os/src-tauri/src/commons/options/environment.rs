use std::{collections::BTreeMap, path::Path};
pub(crate) fn read_env(path: &Path) -> Result<BTreeMap<String, String>, String> {
    // Explicit path only; no expansion, executable syntax or modification of global environment.
    let bytes = std::fs::read(path).map_err(|_| "env_file_unreadable")?;
    if bytes.len() > 65536 {
        return Err("env_file_too_large".into());
    }
    let text = String::from_utf8(bytes).map_err(|_| "invalid_env_encoding")?;
    let mut values = BTreeMap::new();
    for line in text
        .lines()
        .map(str::trim)
        .filter(|s| !s.is_empty() && !s.starts_with('#'))
    {
        let (key, value) = line.split_once('=').ok_or("invalid_env_assignment")?;
        let key = key.trim();
        let mut value = value.trim();
        if value.starts_with('\"') || value.starts_with('\'') {
            if value.len() < 2 || value.as_bytes().last() != value.as_bytes().first() {
                return Err("invalid_env_quotes".into());
            }
            value = &value[1..value.len() - 1];
        }
        if values.insert(key.to_owned(), value.to_owned()).is_some() {
            return Err("duplicate_env_option".into());
        }
    }
    Ok(values)
}
