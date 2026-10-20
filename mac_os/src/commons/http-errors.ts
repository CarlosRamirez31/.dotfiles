import { BackendErrorCode, RejectionReason } from './errors.ts';
const rejectionReasons: Record<BackendErrorCode, RejectionReason> = {
  [BackendErrorCode.ChooseAnotherDefaultVoice]: RejectionReason.DefaultVoice,
  [BackendErrorCode.VoiceProfileCapacity]: RejectionReason.VoiceCapacity,
  [BackendErrorCode.NotFound]: RejectionReason.NotFound,
  [BackendErrorCode.AudioSessionActive]: RejectionReason.Busy,
  [BackendErrorCode.OperationCapacityReached]: RejectionReason.Capacity,
};
export function rejectionReason(value: unknown): RejectionReason {
  if (!value || typeof value !== 'object' || !('error' in value) || typeof value.error !== 'string')
    return RejectionReason.Other;
  return rejectionReasons[value.error as BackendErrorCode] ?? RejectionReason.Other;
}
