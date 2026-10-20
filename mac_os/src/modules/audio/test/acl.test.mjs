import test from 'node:test';
import assert from 'node:assert/strict';
import { audioDevices } from '../infrastructure/acl.ts';
import { InvalidResponseError } from '../../../commons/errors.ts';

test('audio ACL rejects malformed devices and strips external fields', () => {
  assert.deepEqual(
    audioDevices({
      inputs: [{ id: 'input', name: 'Microphone', privateField: 'discard' }],
      blackholeAvailable: true,
      providerData: 'discard',
    }),
    { inputs: [{ id: 'input', name: 'Microphone' }], blackholeAvailable: true },
  );
  for (const value of [
    null,
    {},
    { inputs: [null], blackholeAvailable: true },
    { inputs: [], blackholeAvailable: 'yes' },
  ]) {
    assert.throws(() => audioDevices(value), InvalidResponseError);
  }
});
