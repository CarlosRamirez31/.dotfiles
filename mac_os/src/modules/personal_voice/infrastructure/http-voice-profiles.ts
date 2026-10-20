import { resultOf } from '../../../commons/result';
import type { HttpRequest } from '../../../commons/http';
import { operation, CommandType } from '../../operations/contracts.ts';
import type { VoiceProfilesPort, VoiceEnrollment } from '../application/voice-profiles-port';
import { voiceProfiles } from './acl.ts';
export class HttpVoiceProfiles implements VoiceProfilesPort {
  constructor(private readonly request: HttpRequest) {}
  list(signal: AbortSignal) {
    return resultOf(async () =>
      voiceProfiles(await (await this.request('/voice-profiles', { signal })).json()),
    );
  }
  enroll(value: VoiceEnrollment) {
    return resultOf(async () =>
      operation(
        await (
          await this.request('/commands', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Idempotency-Key': value.key },
            body: JSON.stringify({
              type: CommandType.EnrollVoiceProfile,
              input_id: value.inputId,
              profile_id: value.profileId,
              name: value.name,
              replace: value.replace,
            }),
          })
        ).json(),
      ),
    );
  }
  setDefault(id: string) {
    return resultOf(async () => {
      await this.request(`/voice-profiles/${encodeURIComponent(id)}/default`, { method: 'POST' });
    });
  }
  delete(id: string) {
    return resultOf(async () => {
      await this.request(`/voice-profiles/${encodeURIComponent(id)}`, { method: 'DELETE' });
    });
  }
}
