import { InvalidResponseError } from '../../../commons/errors.ts';
import type { VoiceProfile } from '../domain/voice-profile';
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
export function voiceProfiles(value: unknown): VoiceProfile[] {
  if (!Array.isArray(value) || value.length > 128) throw new InvalidResponseError();
  const profiles = value.map((item): VoiceProfile => {
    if (
      !item ||
      typeof item !== 'object' ||
      typeof item.id !== 'string' ||
      !uuid.test(item.id) ||
      typeof item.name !== 'string' ||
      !item.name.trim() ||
      [...item.name].length > 80 ||
      [...item.name].some((character) => {
        const code = character.codePointAt(0)!;
        return code < 32 || (code >= 127 && code <= 159);
      }) ||
      typeof item.isDefault !== 'boolean' ||
      typeof item.updatedAt !== 'string' ||
      !item.updatedAt.endsWith('Z') ||
      !Number.isFinite(Date.parse(item.updatedAt))
    )
      throw new InvalidResponseError();
    return { id: item.id, name: item.name, isDefault: item.isDefault, updatedAt: item.updatedAt };
  });
  if (
    new Set(profiles.map((p) => p.id)).size !== profiles.length ||
    (profiles.length > 0 && profiles.filter((p) => p.isDefault).length !== 1)
  )
    throw new InvalidResponseError();
  return profiles;
}
