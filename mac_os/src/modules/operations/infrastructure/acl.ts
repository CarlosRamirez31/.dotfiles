import type { Operation } from '../domain/operation';
const statuses = [
  'accepted',
  'running',
  'cancellation_requested',
  'succeeded',
  'failed',
  'cancelled',
  'interrupted',
];
export function operation(value: unknown): Operation {
  if (!value || typeof value !== 'object') throw new Error('invalid_response');
  const v = value as Record<string, unknown>;
  if (
    typeof v.operationId !== 'string' ||
    typeof v.kind !== 'string' ||
    typeof v.status !== 'string' ||
    !statuses.includes(v.status) ||
    (v.detail != null && typeof v.detail !== 'string')
  )
    throw new Error('invalid_response');
  return {
    operationId: v.operationId,
    kind: v.kind,
    status: v.status as Operation['status'],
    detail: v.detail as string | null,
  };
}
