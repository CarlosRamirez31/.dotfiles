import { localConnection, type LocalConnection } from './connection.ts';
import { apiVersion, HttpStatus } from './protocol.ts';
import { RequestRejected } from './errors.ts';
import { rejectionReason } from './http-errors.ts';
import type { ClientLogger } from './logging';
export type HttpRequest = (path: string, init?: RequestInit) => Promise<Response>;

export function createHttp(input: LocalConnection, log: ClientLogger): HttpRequest {
  const connection = localConnection(input);
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
