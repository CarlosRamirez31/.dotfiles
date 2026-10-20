use super::{VoiceStore, acl::decode};
use crate::commons::{AudioErrorCode, Error, Result};
use crate::modules::personal_voice::{application::VoiceProfiles, domain::VoiceProfile};
use rusqlite::OptionalExtension;
pub(super) fn list(store: &VoiceStore) -> Result<Vec<VoiceProfile>> {
    let connection = store.connection()?;
    let mut query = connection.prepare("SELECT id,name,is_default,updated_at FROM voice_profiles ORDER BY is_default DESC,updated_at DESC,id")?;
    query
        .query_map([], |r| {
            Ok(VoiceProfile {
                id: r.get(0)?,
                name: r.get(1)?,
                is_default: r.get(2)?,
                updated_at: r.get(3)?,
            })
        })?
        .collect::<std::result::Result<Vec<_>, _>>()
        .map_err(Into::into)
}

pub(super) fn embedding(store: &VoiceStore, id: &str) -> Result<Vec<f32>> {
    let document: Option<String> = store
        .connection()?
        .query_row(
            "SELECT embedding FROM voice_profiles WHERE id=?1",
            [id],
            |r| r.get(0),
        )
        .optional()?;
    decode(document.ok_or(Error::NotFound)?)
}

pub(super) fn load(store: &VoiceStore) -> Result<Vec<f32>> {
    let id: Option<String> = store
        .connection()?
        .query_row(
            "SELECT id FROM voice_profiles WHERE is_default=1",
            [],
            |r| r.get(0),
        )
        .optional()?;
    store.embedding(&id.ok_or(Error::Audio(AudioErrorCode::VoiceEnrollmentRequired))?)
}
