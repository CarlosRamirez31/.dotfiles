export enum OperationStatus {
  Accepted = 'accepted',
  Running = 'running',
  CancellationRequested = 'cancellation_requested',
  Succeeded = 'succeeded',
  Failed = 'failed',
  Cancelled = 'cancelled',
  Interrupted = 'interrupted',
}

export enum OperationKind {
  StorageCheck = 'diagnostics.check_storage',
  AudioStart = 'audio.start',
  VoiceEnrollment = 'personal_voice.enroll',
}

export enum OperationDetail {
  PreparingVoiceModel = 'preparing_voice_model',
  RecordingEnrollment10Seconds = 'recording_enrollment_10_seconds',
  CreatingVoiceProfile = 'creating_voice_profile',
  VoiceEnrolled = 'voice_enrolled',
  VoiceProfileCapacity = 'voice_profile_capacity',
  VoiceSelectionRequired = 'voice_selection_required',
  AudioActive = 'audio_active',
  AudioStopped = 'audio_stopped',
  IntegrityOk = 'integrity_ok',
  PersonalVoiceRuntimeNotInstalled = 'personal_voice_runtime_not_installed',
  VoiceEnrollmentRequired = 'voice_enrollment_required',
  Blackhole2chNotInstalled = 'blackhole_2ch_not_installed',
  RequiresFloat3248khzMonoOrStereo = 'requires_float32_48khz_mono_or_stereo',
  AudioDeviceOrFormatUnavailable = 'audio_device_or_format_unavailable',
  AudioOverrunOrDeviceLost = 'audio_overrun_or_device_lost',
  AudioOutputBackpressure = 'audio_output_backpressure',
  MicrophoneTimeoutOrPermissionDenied = 'microphone_timeout_or_permission_denied',
  PersonalVoiceModelLoadFailed = 'personal_voice_model_load_failed',
  NoiseProcessingFailed = 'noise_processing_failed',
  PersonalVoiceInferenceFailed = 'personal_voice_inference_failed',
  PersonalVoiceTimeout = 'personal_voice_timeout',
  EnrollmentTooQuiet = 'enrollment_too_quiet',
  ServiceRestarted = 'service_restarted',
}

export function isTerminal(status: OperationStatus): boolean {
  return [
    OperationStatus.Succeeded,
    OperationStatus.Failed,
    OperationStatus.Cancelled,
    OperationStatus.Interrupted,
  ].includes(status);
}
export function canCancel(status: OperationStatus): boolean {
  return status === OperationStatus.Accepted || status === OperationStatus.Running;
}

export interface Operation {
  operationId: string;
  kind: OperationKind;
  status: OperationStatus;
  detail: string | null;
}

export interface OperationEvent {
  eventId: number;
  schemaVersion: number;
  eventType: string;
  operationId: string;
  operation: Operation;
}
