import {
  ABORT_ERROR_NAME,
  AppErrorCode,
  InvalidResponseError,
  RejectionReason,
  RequestRejected,
} from './errors.ts';
export { RequestRejected } from './errors.ts';
export type AppError = { readonly code: AppErrorCode; readonly message: string };
export type Result<T> =
  { readonly ok: true; readonly value: T } | { readonly ok: false; readonly error: AppError };
const rejectionMessages: Record<RejectionReason, string> = {
  [RejectionReason.DefaultVoice]: 'Elige otra voz predeterminada antes de eliminar esta.',
  [RejectionReason.VoiceCapacity]: 'Se alcanzó el máximo configurado de voces.',
  [RejectionReason.NotFound]: 'La voz ya no está disponible. Actualiza la lista.',
  [RejectionReason.Busy]: 'Detén la sesión o el registro actual antes de iniciar otro.',
  [RejectionReason.Capacity]: 'La cola o el historial están llenos. Revisa las operaciones pendientes.',
  [RejectionReason.Other]: 'El servicio no pudo completar la solicitud.',
};
function failure(error: unknown): AppError {
  if (error instanceof RequestRejected)
    return { code: AppErrorCode.Rejected, message: rejectionMessages[error.reason] };
  let code = AppErrorCode.Unavailable;
  if (error instanceof DOMException && error.name === ABORT_ERROR_NAME) code = AppErrorCode.Cancelled;
  if (error instanceof InvalidResponseError) code = AppErrorCode.InvalidResponse;
  return { code, message: 'No se pudo completar la solicitud. Puedes reintentar.' };
}
export async function resultOf<T>(action: () => Promise<T>): Promise<Result<T>> {
  try {
    return { ok: true, value: await action() };
  } catch (error) {
    return { ok: false, error: failure(error) };
  }
}
