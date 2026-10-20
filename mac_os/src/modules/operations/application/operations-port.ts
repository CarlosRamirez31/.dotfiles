import type { Result } from '../../../commons/result';
import type { Operation, OperationEvent } from '../domain/operation';

export interface OperationsPort {
  recent(signal: AbortSignal): Promise<Result<Operation[]>>;
  checkStorage(idempotencyKey: string): Promise<Result<Operation>>;
  cancel(operationId: string): Promise<Result<Operation>>;
  subscribe(
    onEvent: (event: OperationEvent) => void,
    onConnection: (connected: boolean) => void,
    signal: AbortSignal,
  ): Promise<void>;
}
