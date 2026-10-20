import { OperationDetail, OperationStatus, type Operation } from '../../operations/domain/operation.ts';
import type { VoiceProfile } from '../domain/voice-profile';
export enum VoiceDialogAction {
  Create = 'create',
  Replace = 'replace',
  Delete = 'delete',
}
export type VoiceDialog =
  | { kind: VoiceDialogAction.Create }
  | { kind: VoiceDialogAction.Replace | VoiceDialogAction.Delete; profile: VoiceProfile };
const titles: Record<VoiceDialogAction, string> = {
  [VoiceDialogAction.Create]: 'Agregar voz',
  [VoiceDialogAction.Replace]: 'Reemplazar registro de voz',
  [VoiceDialogAction.Delete]: 'Eliminar voz permanentemente',
};
const progressMessages: Partial<Record<OperationDetail, string>> = {
  [OperationDetail.RecordingEnrollment10Seconds]: 'Habla durante 10 segundos.',
  [OperationDetail.CreatingVoiceProfile]: 'Creando el perfil cifrado…',
};
export function dialogTitle(action?: VoiceDialogAction): string {
  return titles[action ?? VoiceDialogAction.Create];
}
export function enrollmentProgress(operation?: Operation): string {
  return progressMessages[operation?.detail as OperationDetail] ?? 'Preparando el modelo local…';
}
export function enrollmentOutcome(operation: Operation, action?: VoiceDialogAction): string {
  if (operation.status === OperationStatus.Succeeded) return 'Voz guardada y cifrada.';
  if (operation.status === OperationStatus.Cancelled) {
    if (action === VoiceDialogAction.Replace) return 'Registro cancelado; se conserva la voz anterior.';
    return 'Registro cancelado; no se creó ninguna voz.';
  }
  if (action === VoiceDialogAction.Replace)
    return 'No se completó el reemplazo; se conserva la voz anterior. Revisa el motivo en las operaciones.';
  return 'No se creó la voz. Revisa el motivo en las operaciones.';
}
export function confirmationLabel(busy: boolean, action?: VoiceDialogAction, retry = false): string {
  if (busy) return 'Procesando…';
  if (action === VoiceDialogAction.Delete) return 'Eliminar permanentemente';
  if (retry) return 'Reintentar la misma solicitud';
  return 'Confirmar e iniciar registro';
}
export function closeLabel(awaiting: boolean, completed: boolean): string {
  if (awaiting) return 'Cancelar registro';
  if (completed) return 'Cerrar';
  return 'Volver';
}
