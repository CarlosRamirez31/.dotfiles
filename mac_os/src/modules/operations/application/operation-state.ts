import { isTerminal, type Operation } from '../domain/operation.ts';
export function mergeOperation(current: Operation[], incoming: Operation): Operation[] {
  const previous = current.find((item) => item.operationId === incoming.operationId);
  // Recent is an authoritative snapshot: replay must not rewind a completed operation.
  if (previous && isTerminal(previous.status)) return current;
  return [incoming, ...current.filter((item) => item.operationId !== incoming.operationId)].slice(0, 100);
}
