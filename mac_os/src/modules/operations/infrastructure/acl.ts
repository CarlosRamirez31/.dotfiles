import { OperationStatus, OperationKind, type Operation } from '../domain/operation.ts';
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
