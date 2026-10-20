import { OperationStatus, OperationKind, type Operation, type OperationEvent } from '../domain/operation.ts';
import { InvalidResponseError } from '../../../commons/errors.ts';
export function operation(value: unknown): Operation {
  if (!value || typeof value !== 'object') throw new InvalidResponseError();
  const v = value as Record<string, unknown>;
  if (
    typeof v.operationId !== 'string' ||
    typeof v.kind !== 'string' ||
    typeof v.status !== 'string' ||
    !Object.values(OperationStatus).includes(v.status as OperationStatus) ||
    !Object.values(OperationKind).includes(v.kind as OperationKind) ||
    (v.detail != null && typeof v.detail !== 'string')
  )
    throw new InvalidResponseError();
  return {
    operationId: v.operationId,
    kind: v.kind as OperationKind,
    status: v.status as Operation['status'],
    detail: v.detail as string | null,
  };
}

export function operationEvent(value: unknown, frameId: string): OperationEvent {
  if (!value || typeof value !== 'object') throw new InvalidResponseError();
  const data = value as Record<string, unknown>;
  if (
    data.schemaVersion !== 1 ||
    !Number.isSafeInteger(data.eventId) ||
    typeof data.eventId !== 'number' ||
    data.eventId < 0 ||
    String(data.eventId) !== frameId ||
    typeof data.eventType !== 'string' ||
    !data.eventType ||
    typeof data.operationId !== 'string'
  ) {
    throw new InvalidResponseError();
  }
  const snapshot = operation(data.operation);
  if (data.operationId !== snapshot.operationId) throw new InvalidResponseError();
  return {
    eventId: data.eventId,
    schemaVersion: 1,
    eventType: data.eventType,
    operationId: data.operationId,
    operation: snapshot,
  };
}
