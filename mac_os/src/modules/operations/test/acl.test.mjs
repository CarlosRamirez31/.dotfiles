import assert from 'node:assert/strict';
import test from 'node:test';
import { operation } from '../infrastructure/acl.ts';
test('ACL validates operation states and drops unknown provider fields', () => {
  const dto = { operationId: 'id', kind: 'audio.start', status: 'accepted', detail: null };
  assert.deepEqual(operation({ ...dto, token: 'secret' }), dto);
  assert.throws(() => operation({ ...dto, status: 'vendor_state' }), /invalid_response/);
  assert.throws(() => operation(null), /invalid_response/);
});
