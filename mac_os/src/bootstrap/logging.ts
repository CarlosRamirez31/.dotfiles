import { invoke } from '@tauri-apps/api/core';
import type { ClientLogger } from '../commons/logging';

export const logClient: ClientLogger = (event, operationId) => {
  // Logging must not break user actions; no exception text or payload is forwarded.
  void invoke('client_log', { event, operationId: operationId ?? null }).catch(() => undefined);
};
