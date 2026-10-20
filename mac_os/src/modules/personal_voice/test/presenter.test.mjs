import assert from 'node:assert/strict';
import test from 'node:test';
import {
  enrollmentOutcome,
  confirmationLabel,
  VoiceDialogAction,
} from '../presentation/voice-profile-presenter.ts';
import { OperationStatus, OperationKind } from '../../operations/domain/operation.ts';
test('voice presenter distinguishes cancelled creation from preserving a replaced voice', () => {
  const operation = {
    operationId: 'local',
    kind: OperationKind.VoiceEnrollment,
    status: OperationStatus.Cancelled,
    detail: null,
  };
  assert.match(enrollmentOutcome(operation, VoiceDialogAction.Create), /no se creó/);
  assert.match(enrollmentOutcome(operation, VoiceDialogAction.Replace), /se conserva/);
  assert.match(
    enrollmentOutcome({ ...operation, status: OperationStatus.Succeeded }, VoiceDialogAction.Replace),
    /guardada/,
  );
  assert.equal(confirmationLabel(false, VoiceDialogAction.Delete), 'Eliminar permanentemente');
});

test('profile selection preserves explicit choice and requires replacing another default before deletion', async () => {
  const { selectedVoice, requiresAnotherDefault } = await import('../application/profile-selection.ts');
  const profiles = [
    { id: 'default', isDefault: true },
    { id: 'other', isDefault: false },
  ];
  assert.equal(selectedVoice(profiles, 'other'), 'other');
  assert.equal(selectedVoice(profiles, 'missing'), 'default');
  assert.equal(selectedVoice([], 'missing'), '');
  assert.equal(requiresAnotherDefault(profiles[0], profiles), true);
  assert.equal(requiresAnotherDefault(profiles[0], [profiles[0]]), false);
});
