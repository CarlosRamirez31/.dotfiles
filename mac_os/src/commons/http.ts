import { apiVersion, LOCAL_PROTOCOL_VERSION, HttpStatus } from './protocol.ts';
import { RequestRejected } from './errors.ts';
import { rejectionReason } from './http-errors.ts';
import type { ClientLogger } from './logging';
export interface LocalConnection {
  endpoint: string;
  token: string;
  protocolVersion: number;
  apiVersion?: string;
}
export type HttpRequest = (path: string, init?: RequestInit) => Promise<Response>;

export function createHttp(connection: LocalConnection, log: ClientLogger): HttpRequest {
  if (connection.protocolVersion !== LOCAL_PROTOCOL_VERSION)
    throw new Error('Versión de servicio incompatible.');
  const version = apiVersion(connection.apiVersion);
  return async (path, init = {}) => {
    const response = await fetch(`${connection.endpoint}/${version}${path}`, {
      ...init,
      headers: { ...init.headers, Authorization: `Bearer ${connection.token}` },
      cache: 'no-store',
      credentials: 'omit',
    });
    if (!response.ok) {
      log('request_failed');
      const body: unknown = await response.json().catch(() => null);
      throw new RequestRejected(rejectionReason(body));
    }
    if (response.status === HttpStatus.Accepted)
      log('request_accepted', response.headers.get('Location')?.split('/').pop());
    return response;
  };
}
