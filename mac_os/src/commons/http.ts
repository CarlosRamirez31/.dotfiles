import { RequestRejected } from './result';
import type { ClientLogger } from './logging';
export interface LocalConnection {
  endpoint: string;
  token: string;
  protocolVersion: number;
}
export type HttpRequest = (path: string, init?: RequestInit) => Promise<Response>;

export function createHttp(connection: LocalConnection, log: ClientLogger): HttpRequest {
  if (connection.protocolVersion !== 1) throw new Error('Versión de servicio incompatible.');
  return async (path, init = {}) => {
    const response = await fetch(`${connection.endpoint}/v1${path}`, {
      ...init,
      headers: { ...init.headers, Authorization: `Bearer ${connection.token}` },
      cache: 'no-store',
      credentials: 'omit',
    });
    if (!response.ok) {
      log('request_failed');
      const body = (await response.json().catch(() => null)) as { error?: string } | null;
      throw new RequestRejected(
        body?.error === 'audio_session_active'
          ? 'busy'
          : body?.error === 'operation_capacity_reached'
            ? 'capacity'
            : 'other',
      );
    }
    if (response.status === 202) log('request_accepted', response.headers.get('Location')?.split('/').pop());
    return response;
  };
}
