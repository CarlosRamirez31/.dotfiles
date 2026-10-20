export type AppError = {
  readonly code: 'unavailable' | 'invalid_response' | 'cancelled' | 'rejected';
  readonly message: string;
};
export type Result<T> =
  { readonly ok: true; readonly value: T } | { readonly ok: false; readonly error: AppError };
export class RequestRejected extends Error {
  readonly reason: 'busy' | 'capacity' | 'other';
  constructor(reason: 'busy' | 'capacity' | 'other') {
    super('request_rejected');
    this.reason = reason;
  }
}
export async function resultOf<T>(action: () => Promise<T>): Promise<Result<T>> {
  try {
    return { ok: true, value: await action() };
  } catch (error) {
    if (error instanceof RequestRejected)
      return {
        ok: false,
        error: {
          code: 'rejected',
          message:
            error.reason === 'busy'
              ? 'Detén la sesión o el registro actual antes de iniciar otro.'
              : error.reason === 'capacity'
                ? 'La cola o el historial están llenos. Revisa las operaciones pendientes.'
                : 'El servicio no pudo completar la solicitud.',
        },
      };
    return {
      ok: false,
      error: {
        code:
          error instanceof DOMException && error.name === 'AbortError'
            ? 'cancelled'
            : error instanceof Error && error.message === 'invalid_response'
              ? 'invalid_response'
              : 'unavailable',
        message: 'No se pudo completar la solicitud. Puedes reintentar.',
      },
    };
  }
}
