import assert from 'node:assert/strict';
import test from 'node:test';
import { rejectionReason } from '../http-errors.ts';
import { BackendErrorCode, RejectionReason } from '../errors.ts';
import { createHttp } from '../http.ts';
test('HTTP ACL maps known errors and sanitizes unknown provider payloads', () => {
  assert.equal(rejectionReason({ error: BackendErrorCode.AudioSessionActive }), RejectionReason.Busy);
  assert.equal(
    rejectionReason({ error: BackendErrorCode.ChooseAnotherDefaultVoice }),
    RejectionReason.DefaultVoice,
  );
  assert.equal(
    rejectionReason({ error: 'unexpected_provider_payload', embedding: [1] }),
    RejectionReason.Other,
  );
  assert.equal(rejectionReason(null), RejectionReason.Other);
});
test('HTTP uses the handshake API prefix and validates it before any request', async (context) => {
  let requested = '';
  context.mock.method(globalThis, 'fetch', async (url) => {
    requested = url;
    return new globalThis.Response('[]');
  });
  const http = createHttp(
    { endpoint: 'http://127.0.0.1:1234', token: 'test-only', protocolVersion: 1, apiVersion: 'v7' },
    () => {},
  );
  await http('/voice-profiles');
  assert.equal(requested, 'http://127.0.0.1:1234/v7/voice-profiles');
  const defaultHttp = createHttp(
    { endpoint: 'http://127.0.0.1:1234', token: 'test-only', protocolVersion: 1 },
    () => {},
  );
  await defaultHttp('/operations');
  assert.equal(requested, 'http://127.0.0.1:1234/v1/operations');
  assert.throws(
    () =>
      createHttp(
        { endpoint: 'http://127.0.0.1:1234', token: 'test-only', protocolVersion: 1, apiVersion: '../v1' },
        () => {},
      ),
    /API inválida/,
  );
});

test('native connection ACL rejects untrusted endpoints before making a request', () => {
  for (const endpoint of [
    'https://external.example',
    'http://127.0.0.1:80@external.example',
    'http://127.0.0.1:1234/path',
    'not-a-url',
  ]) {
    assert.throws(() => createHttp({ endpoint, token: 'test-only', protocolVersion: 1 }, () => {}));
  }
});
