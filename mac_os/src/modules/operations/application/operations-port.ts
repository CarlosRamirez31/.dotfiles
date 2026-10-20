import type { Operation, OperationEvent } from '../domain/operation';

export interface OperationsPort {
  recent(signal: AbortSignal): Promise<Operation[]>;
  checkStorage(idempotencyKey: string): Promise<Operation>;
  cancel(operationId: string): Promise<Operation>;
  subscribe(
    onEvent: (event: OperationEvent) => void,
    onConnection: (connected: boolean) => void,
    signal: AbortSignal,
  ): Promise<void>;
}
