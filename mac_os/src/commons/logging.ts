export type ClientEvent =
  'connected' | 'connection_lost' | 'request_failed' | 'startup_failed' | 'request_accepted';
export type ClientLogger = (event: ClientEvent, operationId?: string) => void;
