import type { VoiceProfile } from '../domain/voice-profile';

export function selectedVoice(profiles: VoiceProfile[], current: string): string {
  if (profiles.some((profile) => profile.id === current)) return current;
  return profiles.find((profile) => profile.isDefault)?.id ?? '';
}
export function requiresAnotherDefault(profile: VoiceProfile, profiles: VoiceProfile[]): boolean {
  return profile.isDefault && profiles.length > 1;
}
