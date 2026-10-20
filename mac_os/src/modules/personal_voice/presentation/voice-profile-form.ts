import type { VoiceEnrollment } from '../application/voice-profiles-port';
import { VoiceDialogAction, type VoiceDialog } from './voice-profile-presenter.ts';

export function dialogProfileName(dialog: VoiceDialog | null): string {
  if (!dialog || dialog.kind === VoiceDialogAction.Create) return '';
  return dialog.profile.name;
}
export function enrollmentRequest(
  dialog: Exclude<VoiceDialog, { kind: VoiceDialogAction.Delete }>,
  input: string,
  name: string,
  createId: () => string,
): VoiceEnrollment {
  let profileId: string;
  if (dialog.kind === VoiceDialogAction.Create) profileId = createId();
  else profileId = dialog.profile.id;
  return {
    inputId: input,
    profileId,
    name: name.trim(),
    replace: dialog.kind === VoiceDialogAction.Replace,
    key: createId(),
  };
}
