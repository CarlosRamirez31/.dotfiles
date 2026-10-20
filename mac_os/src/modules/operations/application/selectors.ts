import { OperationKind, isTerminal, type Operation } from '../domain/operation.ts';
export function enrollmentRevision(items: Operation[]): string {
  return items
    .filter((item) => item.kind === OperationKind.VoiceEnrollment)
    .map((item) => `${item.operationId}:${item.status}`)
    .join('|');
}
export function hasActiveAudio(items: Operation[]): boolean {
  return items.some((item) => item.kind !== OperationKind.StorageCheck && !isTerminal(item.status));
}
