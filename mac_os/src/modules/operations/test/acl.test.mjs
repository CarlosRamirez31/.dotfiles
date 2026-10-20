import assert from 'node:assert/strict';
import test from 'node:test';
import { operation } from '../infrastructure/acl.ts';
test('ACL validates operation states and drops unknown provider fields', () => {
  const dto = { operationId: 'id', kind: 'audio.start', status: 'accepted', detail: null };
  assert.deepEqual(operation({ ...dto, token: 'secret' }), dto);
  assert.throws(() => operation({ ...dto, status: 'vendor_state' }), /invalid_response/);
  assert.throws(() => operation(null), /invalid_response/);
});

test('event ACL validates correlation and drops provider metadata', async () => {
  const { operationEvent } = await import('../infrastructure/acl.ts');
  const dto = { operationId: 'id', kind: 'audio.start', status: 'accepted', detail: null };
  const envelope = {
    eventId: 12,
    schemaVersion: 1,
    eventType: 'operation.accepted',
    operationId: 'id',
    operation: dto,
  };
  assert.deepEqual(operationEvent({ ...envelope, privateData: 'discard' }, '12'), envelope);
  assert.throws(() => operationEvent({ ...envelope, operationId: 'other' }, '12'));
  assert.throws(() => operationEvent({ ...envelope, operation: null }, '12'));
  assert.throws(() => operationEvent(envelope, '13'));
  assert.throws(() => operationEvent({ ...envelope, eventType: null }, '12'));
});
