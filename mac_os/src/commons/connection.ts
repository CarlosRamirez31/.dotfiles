import { InvalidResponseError } from './errors.ts';
import { apiVersion, LOCAL_PROTOCOL_VERSION } from './protocol.ts';

export interface LocalConnection {
  endpoint: string;
  token: string;
  protocolVersion: number;
  apiVersion?: string;
}

/** ACL for the native handshake; never trust an invoke generic as runtime validation. */
export function localConnection(value: unknown): LocalConnection {
  if (!value || typeof value !== 'object') throw new InvalidResponseError();
  const data = value as Record<string, unknown>;
  if (
    typeof data.endpoint !== 'string' ||
    typeof data.token !== 'string' ||
    !data.token ||
    typeof data.protocolVersion !== 'number' ||
    (data.apiVersion !== undefined && typeof data.apiVersion !== 'string')
  )
    throw new InvalidResponseError();
  if (data.protocolVersion !== LOCAL_PROTOCOL_VERSION) throw new Error('Versión de servicio incompatible.');
  let endpoint: URL;
  try {
    endpoint = new URL(data.endpoint);
  } catch {
    throw new InvalidResponseError();
  }
  if (
    endpoint.protocol !== 'http:' ||
    endpoint.hostname !== '127.0.0.1' ||
    endpoint.username ||
    endpoint.password ||
    endpoint.pathname !== '/' ||
    endpoint.search ||
    endpoint.hash
  ) {
    throw new InvalidResponseError();
  }
  return {
    endpoint: data.endpoint,
    token: data.token,
    protocolVersion: data.protocolVersion,
    apiVersion: apiVersion(data.apiVersion),
  };
}
