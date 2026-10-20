import assert from 'node:assert/strict';
import test from 'node:test';
import { SseParser } from '../sse.ts';

test('SSE supports every character boundary, CRLF, comments and multiline data', () => {
  const parser = new SseParser();
  const events = [];
  for (const character of ':keepalive\r\n\r\nid: 42\r\nevent: operation.started\r\ndata: first\r\ndata: second\r\n\r\n') {
    events.push(...parser.push(character));
  }
  assert.deepEqual(events, [{ id: '42', data: 'first\nsecond' }]);
});

test('SSE bounds incomplete frames and multiline payloads', () => {
  assert.throws(() => new SseParser().push('a'.repeat(65537)), /event_too_large/);
  const parser = new SseParser();
  assert.throws(() => {
    for (let i = 0; i < 100; i++) parser.push(`data: ${'a'.repeat(1000)}\n`);
  }, /event_too_large/);
});
