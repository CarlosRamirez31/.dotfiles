import { InvalidResponseError } from '../../../commons/errors.ts';
import { resultOf } from '../../../commons/result';
import type { AudioPort, AudioDevices } from '../application/audio-port';
import type { HttpRequest } from '../../../commons/http';

export class HttpAudio implements AudioPort {
  constructor(private readonly request: HttpRequest) {}
  async devices(signal: AbortSignal): Promise<import('../../../commons/result').Result<AudioDevices>> {
    return resultOf(async () => {
      const value: unknown = await (await this.request('/audio/devices', { signal })).json();
      if (
        !value ||
        typeof value !== 'object' ||
        !('inputs' in value) ||
        !Array.isArray(value.inputs) ||
        !('blackholeAvailable' in value) ||
        typeof value.blackholeAvailable !== 'boolean' ||
        value.inputs.some((x) => !x || typeof x.id !== 'string' || typeof x.name !== 'string')
      )
        throw new InvalidResponseError();
      return {
        inputs: value.inputs.map((x) => ({ id: x.id, name: x.name })),
        blackholeAvailable: value.blackholeAvailable,
      };
    });
  }
  private async command(command: object, key: string) {
    return resultOf(async () => {
      await this.request('/commands', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Idempotency-Key': key },
        body: JSON.stringify(command),
      });
    });
  }
  start(inputId: string, personalVoice: boolean, key: string, voiceProfileId?: string) {
    if (personalVoice && voiceProfileId)
      return this.command(
        { type: 'start_voice_profile_audio', input_id: inputId, voice_profile_id: voiceProfileId },
        key,
      );
    return this.command({ type: 'start_audio', input_id: inputId, personal_voice: personalVoice }, key);
  }
  enroll(inputId: string, key: string) {
    return this.command({ type: 'enroll_voice', input_id: inputId }, key);
  }
}
