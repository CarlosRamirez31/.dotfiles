// Public boundary for consumers of operation responses; implementation stays module-owned.
export { operation } from './infrastructure/acl.ts';
export type { Operation } from './domain/operation.ts';
export enum CommandType {
  StartAudio = 'start_audio',
  StartVoiceProfileAudio = 'start_voice_profile_audio',
  EnrollVoice = 'enroll_voice',
  EnrollVoiceProfile = 'enroll_voice_profile',
}
