import type { Result } from '../../../commons/result';
export interface AudioDevices {
  inputs: { id: string; name: string }[];
  blackholeAvailable: boolean;
}
export interface AudioPort {
  devices(signal: AbortSignal): Promise<Result<AudioDevices>>;
  start(
    inputId: string,
    personalVoice: boolean,
    idempotencyKey: string,
    voiceProfileId?: string,
  ): Promise<Result<void>>;
  enroll(inputId: string, idempotencyKey: string): Promise<Result<void>>;
}
