export enum AppErrorCode {
  Unavailable = 'unavailable',
  InvalidResponse = 'invalid_response',
  Cancelled = 'cancelled',
  Rejected = 'rejected',
}
export enum RejectionReason {
  Busy = 'busy',
  Capacity = 'capacity',
  DefaultVoice = 'default_voice',
  VoiceCapacity = 'voice_capacity',
  NotFound = 'not_found',
  Other = 'other',
}
export enum BackendErrorCode {
  AudioSessionActive = 'audio_session_active',
  OperationCapacityReached = 'operation_capacity_reached',
  ChooseAnotherDefaultVoice = 'choose_another_default_voice',
  VoiceProfileCapacity = 'voice_profile_capacity',
  NotFound = 'not_found',
}
export class InvalidResponseError extends Error {
  constructor() {
    super(AppErrorCode.InvalidResponse);
  }
}
export class RequestRejected extends Error {
  constructor(readonly reason: RejectionReason) {
    super(AppErrorCode.Rejected);
  }
}
export const ABORT_ERROR_NAME = 'AbortError';
