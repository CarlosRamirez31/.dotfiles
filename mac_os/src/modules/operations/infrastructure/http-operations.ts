import { SNAPSHOT_CURSOR_HEADER } from '../../../commons/protocol.ts';
import { InvalidResponseError } from '../../../commons/errors.ts';
import type { ClientOptions } from '../../../commons/options';
import { resultOf, type Result } from '../../../commons/result';
import { operation } from './acl.ts';
import type { ClientLogger } from '../../../commons/logging';
import type { OperationsPort } from '../application/operations-port';
import type { Operation, OperationEvent } from '../domain/operation';
import { SseParser } from '../../../commons/sse';

import type { HttpRequest } from '../../../commons/http';

export class HttpOperations implements OperationsPort {
  private snapshotCursor = '0';
  constructor(
    private readonly request: HttpRequest,
    private readonly log: ClientLogger,
    private readonly options: ClientOptions,
  ) {}

  async recent(signal: AbortSignal): Promise<Result<Operation[]>> {
    return resultOf(async () => {
      const response = await this.request('/operations', {
        signal,
        headers: { [SNAPSHOT_CURSOR_HEADER]: '1' },
      });
      const value: unknown = await response.json();
      if (!Array.isArray(value)) throw new InvalidResponseError();
      const items = value.map(operation);
      const cursor = response.headers.get(SNAPSHOT_CURSOR_HEADER);
      if (cursor && /^\d+$/.test(cursor)) this.snapshotCursor = cursor;
      return items;
    });
  }

  async checkStorage(idempotencyKey: string): Promise<Result<Operation>> {
    return resultOf(async () =>
      operation(
        await (
          await this.request('/operations/storage-check', {
            method: 'POST',
            headers: { 'Idempotency-Key': idempotencyKey },
          })
        ).json(),
      ),
    );
  }

  async cancel(operationId: string): Promise<Result<Operation>> {
    return resultOf(async () =>
      operation(
        await (
          await this.request(`/operations/${encodeURIComponent(operationId)}/cancel`, { method: 'POST' })
        ).json(),
      ),
    );
  }

  async subscribe(
    onEvent: (event: OperationEvent) => void,
    onConnection: (connected: boolean) => void,
    signal: AbortSignal,
  ): Promise<void> {
    let cursor = this.snapshotCursor;
    let wasConnected = false;
    while (!signal.aborted) {
      try {
        const response = await this.request('/events', { signal, headers: { 'Last-Event-ID': cursor } });
        if (!response.body) throw new Error('events_unavailable');
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        const parser = new SseParser();
        onConnection(true);
        if (!wasConnected) this.log('connected');
        wasConnected = true;
        try {
          while (!signal.aborted) {
            const { value, done } = await reader.read();
            if (done) break;
            for (const frame of parser.push(decoder.decode(value, { stream: true }))) {
              const event = JSON.parse(frame.data) as OperationEvent;
              if (
                event.schemaVersion !== 1 ||
                String(event.eventId) !== frame.id ||
                event.operationId !== event.operation.operationId
              ) {
                throw new Error('invalid_event');
              }
              event.operation = operation(event.operation);
              onEvent(event);
              cursor = frame.id;
            }
          }
        } finally {
          await reader.cancel();
          reader.releaseLock();
        }
      } catch {
        if (signal.aborted) return;
      }
      if (signal.aborted) return;
      onConnection(false);
      if (wasConnected) this.log('connection_lost');
      wasConnected = false;
      await new Promise<void>((resolve) => {
        const finish = () => {
          clearTimeout(timer);
          signal.removeEventListener('abort', finish);
          resolve();
        };
        const timer = setTimeout(finish, this.options.reconnectMs);
        signal.addEventListener('abort', finish, { once: true });
      });
    }
  }
}
