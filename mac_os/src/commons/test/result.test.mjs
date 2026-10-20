import assert from 'node:assert/strict';
import test from 'node:test';
import { InvalidResponseError } from '../errors.ts';
import { resultOf } from '../result.ts';
test('Result sanitizes exceptions and distinguishes invalid provider responses', async () => {
  assert.deepEqual(await resultOf(async () => 42), { ok: true, value: 42 });
  const failure = await resultOf(async () => {
    throw new Error('secret');
  });
  assert.equal(failure.ok, false);
  assert.equal(JSON.stringify(failure).includes('secret'), false);
  const invalid = await resultOf(async () => {
    throw new InvalidResponseError();
  });
  assert.equal(invalid.error.code, 'invalid_response');
});

import { clientOptions } from '../options.ts';
test('Public Options are validated, immutable and discard private fields', () => {
  const options = clientOptions({ reconnectMs: 1500, token: 'secret' });
  assert.deepEqual(options, { reconnectMs: 1500 });
  assert.equal(Object.isFrozen(options), true);
  assert.throws(() => clientOptions({ reconnectMs: NaN }), /invalid_client_options/);
});
