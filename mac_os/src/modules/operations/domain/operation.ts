export type OperationStatus =
  'accepted' | 'running' | 'cancellation_requested' | 'succeeded' | 'failed' | 'cancelled' | 'interrupted';

export interface Operation {
  operationId: string;
  kind: string;
  status: OperationStatus;
  detail: string | null;
}

export interface OperationEvent {
  eventId: number;
  schemaVersion: number;
  eventType: string;
  operationId: string;
  operation: Operation;
}
