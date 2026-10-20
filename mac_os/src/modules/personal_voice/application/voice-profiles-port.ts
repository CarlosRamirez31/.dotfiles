import type { Result } from '../../../commons/result';
import type { Operation } from '../../operations/domain/operation';
import type { VoiceProfile } from '../domain/voice-profile';
export interface VoiceEnrollment {
  inputId: string;
  profileId: string;
  name: string;
  replace: boolean;
  key: string;
}
export interface VoiceProfilesPort {
  list(signal: AbortSignal): Promise<Result<VoiceProfile[]>>;
  enroll(request: VoiceEnrollment): Promise<Result<Operation>>;
  setDefault(id: string): Promise<Result<void>>;
  delete(id: string): Promise<Result<void>>;
}
