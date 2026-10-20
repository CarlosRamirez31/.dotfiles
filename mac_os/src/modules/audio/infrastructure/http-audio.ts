import type { AudioPort, AudioDevices } from '../application/audio-port';
import type { HttpRequest } from '../../../commons/http';

export class HttpAudio implements AudioPort {
  constructor(private readonly request: HttpRequest) {}
  async devices(signal: AbortSignal): Promise<AudioDevices> {
    return (await this.request('/audio/devices', { signal })).json();
  }
  private async command(command: object, key: string) {
    await this.request('/commands', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Idempotency-Key': key },
      body: JSON.stringify(command),
    });
  }
  start(inputId: string, personalVoice: boolean, key: string) {
    return this.command({ type: 'start_audio', input_id: inputId, personal_voice: personalVoice }, key);
  }
  enroll(inputId: string, key: string) {
    return this.command({ type: 'enroll_voice', input_id: inputId }, key);
  }
}
