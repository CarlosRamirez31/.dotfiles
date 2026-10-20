export interface AudioDevices {
  inputs: { id: string; name: string }[];
  blackholeAvailable: boolean;
}
export interface AudioPort {
  devices(signal: AbortSignal): Promise<AudioDevices>;
  start(inputId: string, personalVoice: boolean, idempotencyKey: string): Promise<void>;
  enroll(inputId: string, idempotencyKey: string): Promise<void>;
}
