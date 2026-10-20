use crate::commons::{Command, Error, Result};

pub(crate) fn validate_command(key: &str, command: &Command) -> Result<()> {
    if key.is_empty()
        || key.len() > 128
        || !key.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'-')
    {
        return Err(Error::Invalid);
    }
    match command {
        Command::StartAudio { input_id, .. }
        | Command::EnrollVoice { input_id }
        | Command::StartVoiceProfileAudio { input_id, .. }
        | Command::EnrollVoiceProfile { input_id, .. }
            if input_id.is_empty() || input_id.len() > 512 =>
        {
            return Err(Error::Invalid);
        }
        _ => {}
    }
    match command {
        Command::EnrollVoiceProfile {
            profile_id, name, ..
        } => crate::modules::personal_voice::domain::validate(profile_id, name)?,
        Command::StartVoiceProfileAudio {
            voice_profile_id, ..
        } if uuid::Uuid::parse_str(voice_profile_id).is_err() => return Err(Error::Invalid),
        _ => {}
    }

    Ok(())
}
