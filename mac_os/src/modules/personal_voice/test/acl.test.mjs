import assert from 'node:assert/strict';
import test from 'node:test';
import { voiceProfiles } from '../infrastructure/acl.ts';
const profile = {
  id: '00000000-0000-4000-8000-000000000001',
  name: 'Voz anterior',
  isDefault: true,
  updatedAt: '2026-10-20T23:00:00.000Z',
};
test('voice ACL excludes embeddings and rejects ambiguous defaults or duplicate identifiers', () => {
  assert.deepEqual(voiceProfiles([{ ...profile, embedding: [0.1], sdk: 'private' }]), [profile]);
  assert.deepEqual(voiceProfiles([]), []);
  assert.throws(() => voiceProfiles([{ ...profile, isDefault: false }]), /invalid_response/);
  assert.throws(() => voiceProfiles([profile, profile]), /invalid_response/);
  assert.throws(() => voiceProfiles([{ ...profile, updatedAt: 'vendor-date' }]), /invalid_response/);
  assert.throws(() => voiceProfiles([{ ...profile, name: '\n' }]), /invalid_response/);
});
