import assert from 'node:assert/strict';
import test from 'node:test';
import { mergeOperation } from '../application/operation-state.ts';
import { OperationStatus, OperationKind } from '../domain/operation.ts';
const completed = {
  operationId: 'known',
  kind: OperationKind.VoiceEnrollment,
  status: OperationStatus.Succeeded,
  detail: null,
};
test('SSE replay cannot rewind a completed snapshot or recreate an active registration', () => {
  const current = [completed];
  assert.equal(mergeOperation(current, { ...completed, status: OperationStatus.Accepted }), current);
  assert.equal(mergeOperation(current, { ...completed, status: OperationStatus.Running }), current);
  const updated = mergeOperation([{ ...completed, status: OperationStatus.Running }], completed);
  assert.equal(updated[0].status, OperationStatus.Succeeded);
});
