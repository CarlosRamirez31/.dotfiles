use super::{VoiceStore, session_guard::idle};
use crate::commons::{AudioErrorCode, Error, Result};
use crate::modules::personal_voice::{application::VoiceProfiles, domain::validate};
use rusqlite::{OptionalExtension, TransactionBehavior, params};
pub(super) fn save_profile(
    store: &VoiceStore,
    id: &str,
    name: &str,
    embedding: &[f32],
    replace: bool,
) -> Result<()> {
    validate(id, name)?;
    if embedding.len() != 192 || embedding.iter().any(|x| !x.is_finite()) {
        return Err(Error::Invalid);
    }
    let document = serde_json::to_string(embedding).map_err(|_| Error::Storage)?;
    let mut connection = store.connection()?;
    let tx = connection.transaction_with_behavior(TransactionBehavior::Immediate)?;
    if replace {
        if tx.execute("UPDATE voice_profiles SET name=?2,embedding=?3,updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id=?1",params![id,name.trim(),document])? == 0 { return Err(Error::NotFound); }
    } else {
        let count: i64 = tx.query_row("SELECT count(*) FROM voice_profiles", [], |r| r.get(0))?;
        if count >= store.max_profiles as i64 {
            return Err(Error::Audio(AudioErrorCode::VoiceProfileCapacity));
        }
        let exists: bool = tx.query_row(
            "SELECT EXISTS(SELECT 1 FROM voice_profiles WHERE id=?1)",
            [id],
            |r| r.get(0),
        )?;
        if exists {
            return Err(Error::Conflict);
        }
        tx.execute(
            "INSERT INTO voice_profiles VALUES(?1,?2,?3,?4,strftime('%Y-%m-%dT%H:%M:%fZ','now'))",
            params![id, name.trim(), document, count == 0],
        )?;
    }
    tx.commit()?;
    tracing::info!(target:"business", event_type="voice_profile.saved", profile_id=id, replaced=replace);
    Ok(())
}

pub(super) fn set_default(store: &VoiceStore, id: &str) -> Result<()> {
    let mut connection = store.connection()?;
    let tx = connection.transaction_with_behavior(TransactionBehavior::Immediate)?;
    idle(&tx)?;
    let exists: bool = tx.query_row(
        "SELECT EXISTS(SELECT 1 FROM voice_profiles WHERE id=?1)",
        [id],
        |r| r.get(0),
    )?;
    if !exists {
        return Err(Error::NotFound);
    }
    tx.execute(
        "UPDATE voice_profiles SET is_default=0 WHERE is_default=1",
        [],
    )?;
    tx.execute("UPDATE voice_profiles SET is_default=1 WHERE id=?1", [id])?;
    tx.commit()?;
    tracing::info!(target:"business",event_type="voice_profile.default_changed",profile_id=id);
    Ok(())
}

pub(super) fn delete(store: &VoiceStore, id: &str) -> Result<()> {
    let mut connection = store.connection()?;
    let tx = connection.transaction_with_behavior(TransactionBehavior::Immediate)?;
    idle(&tx)?;
    let is_default: Option<bool> = tx
        .query_row(
            "SELECT is_default FROM voice_profiles WHERE id=?1",
            [id],
            |r| r.get(0),
        )
        .optional()?;
    // Deletion retries are harmless and never remove a different voice.
    let Some(is_default) = is_default else {
        return Ok(());
    };
    let count: i64 = tx.query_row("SELECT count(*) FROM voice_profiles", [], |r| r.get(0))?;
    if is_default && count > 1 {
        return Err(Error::Audio(AudioErrorCode::ChooseAnotherDefaultVoice));
    }
    tx.execute("DELETE FROM voice_profiles WHERE id=?1", [id])?;
    tx.commit()?;
    tracing::info!(target:"business",event_type="voice_profile.deleted",profile_id=id);
    Ok(())
}

pub(super) fn save(store: &VoiceStore, embedding: &[f32]) -> Result<()> {
    let profiles = store.list()?;
    match profiles.as_slice() {
        [] => store.save_profile(
            &uuid::Uuid::new_v4().to_string(),
            "Mi voz",
            embedding,
            false,
        ),
        [one] => store.save_profile(&one.id, &one.name, embedding, true),
        _ => Err(Error::Audio(AudioErrorCode::VoiceSelectionRequired)),
    }
}
