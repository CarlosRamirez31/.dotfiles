export const DEFAULT_API_VERSION = 'v1';
export const LOCAL_PROTOCOL_VERSION = 1;
export const SNAPSHOT_CURSOR_HEADER = 'X-Event-Cursor';
export enum HttpStatus {
  Accepted = 202,
}
export function apiVersion(value: string | undefined): string {
  const version = value ?? DEFAULT_API_VERSION;
  if (!/^v[1-9]\d{0,2}$/.test(version)) throw new Error('Versión de API inválida.');
  return version;
}
