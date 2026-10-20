export interface ClientOptions {
  readonly reconnectMs: number;
}
export function clientOptions(value: unknown): ClientOptions {
  if (
    !value ||
    typeof value !== 'object' ||
    !('reconnectMs' in value) ||
    typeof value.reconnectMs !== 'number' ||
    !Number.isInteger(value.reconnectMs) ||
    value.reconnectMs < 100 ||
    value.reconnectMs > 30000
  )
    throw new Error('invalid_client_options');
  return Object.freeze({ reconnectMs: value.reconnectMs });
}
