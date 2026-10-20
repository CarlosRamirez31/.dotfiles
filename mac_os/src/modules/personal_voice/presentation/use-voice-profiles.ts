import { useAudioInputs } from '../../audio/presentation/use-audio-inputs';
import { useVoiceCatalog } from './use-voice-catalog';
import { enrollmentRevision, hasActiveAudio } from '../../operations/application/selectors';
import { requiresAnotherDefault } from '../application/profile-selection';
import { dialogProfileName, enrollmentRequest } from './voice-profile-form';
import { useEffect, useState, type ChangeEvent, type SyntheticEvent } from 'react';
import type { VoiceProfilesPort, VoiceEnrollment } from '../application/voice-profiles-port';
import { isTerminal, type Operation } from '../../operations/domain/operation.ts';
import type { OperationsPort } from '../../operations/application/operations-port';
import type { AudioPort } from '../../audio/application/audio-port';
import { AppErrorCode } from '../../../commons/errors.ts';
import {
  VoiceDialogAction,
  type VoiceDialog,
  dialogTitle,
  enrollmentProgress,
  enrollmentOutcome,
  confirmationLabel,
  closeLabel,
} from './voice-profile-presenter.ts';
export interface VoiceProfilesProps {
  profiles: VoiceProfilesPort;
  audio: AudioPort;
  operations: OperationsPort;
  items: Operation[];
  onSelect: (id: string) => void;
}
export function useVoiceProfiles({ profiles, audio, operations, items, onSelect }: VoiceProfilesProps) {
  const [modal, setModal] = useState<VoiceDialog | null>(null);
  const [name, setName] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [retry, setRetry] = useState<VoiceEnrollment | null>(null);
  const [pendingId, setPendingId] = useState('');
  const { rows, selected, setSelected, loading, refresh } = useVoiceCatalog(
    profiles,
    enrollmentRevision(items),
    setMessage,
  );
  const { input, setInput, inputs } = useAudioInputs(audio);
  const active = hasActiveAudio(items);
  const pending = items.find((item) => item.operationId === pendingId);
  useEffect(() => {
    onSelect(selected);
  }, [selected, onSelect]);
  function open(value: VoiceDialog) {
    setMessage('');
    setName(dialogProfileName(value));
    setRetry(null);
    setPendingId('');
    setModal(value);
  }
  async function makeDefault(id: string) {
    setBusy(true);
    setMessage('');
    const result = await profiles.setDefault(id);
    if (result.ok) {
      setSelected(id);
      refresh();
    } else setMessage(result.error.message);
    setBusy(false);
  }
  async function submit() {
    if (!modal || busy) return;
    setBusy(true);
    setMessage('');
    if (modal.kind === VoiceDialogAction.Delete) {
      const result = await profiles.delete(modal.profile.id);
      if (result.ok) {
        setModal(null);
        refresh();
        setMessage('Voz eliminada de la aplicación.');
      } else setMessage(result.error.message);
    } else {
      const request = retry ?? enrollmentRequest(modal, input, name, () => crypto.randomUUID());
      setRetry(request);
      const result = await profiles.enroll(request);
      if (result.ok) {
        setPendingId(result.value.operationId);
        setRetry(null);
      } else {
        setMessage(result.error.message);
        if (result.error.code === AppErrorCode.Rejected) setRetry(null);
      }
    }
    setBusy(false);
  }
  async function close() {
    if (pendingId && (!pending || !isTerminal(pending.status))) {
      const result = await operations.cancel(pendingId);
      setMessage(
        result.ok ? 'Cancelación solicitada; espera la confirmación del servicio.' : result.error.message,
      );
    } else {
      setModal(null);
      setPendingId('');
      setRetry(null);
    }
  }
  const completed = pending && isTerminal(pending.status);
  const awaiting = !!pendingId && !completed;
  const deleting = modal?.kind === VoiceDialogAction.Delete;
  const replacing = modal?.kind === VoiceDialogAction.Replace;
  const deleteBlocked = deleting && requiresAnotherDefault(modal.profile, rows);
  let confirmDisabled = busy || active || loading;
  if (deleting) confirmDisabled ||= deleteBlocked;
  else confirmDisabled ||= !input || !name.trim();
  const fieldsDisabled = busy || awaiting || !!retry || !!completed;
  const viewRows = rows.map((profile) => ({
    ...profile,
    canMakeDefault: !profile.isDefault,
    selected: selected === profile.id,
    label: profile.name + (profile.isDefault ? ' · Predeterminada' : ''),
    select: () => setSelected(profile.id),
    makeDefault: () => void makeDefault(profile.id),
    edit: () => open({ kind: VoiceDialogAction.Replace, profile }),
    delete: () => open({ kind: VoiceDialogAction.Delete, profile }),
  }));
  return {
    rows: viewRows,
    empty: !loading && rows.length === 0,
    managementDisabled: active || busy,
    addDisabled: active || busy || loading,
    outsideMessage: modal ? '' : message,
    profileName: dialogProfileName(modal),
    showConfirm: !pendingId,
    modal,
    name,
    input,
    inputs,
    message,
    busy,
    active,
    loading,
    modalOpen: !!modal,
    awaiting,
    completed: !!completed,
    pendingId,
    fieldsDisabled,
    confirmDisabled,
    deleteBlocked,
    deleting,
    replacing,
    title: dialogTitle(modal?.kind),
    progress: enrollmentProgress(pending),
    outcome: pending ? enrollmentOutcome(pending, modal?.kind) : '',
    submitLabel: confirmationLabel(busy, modal?.kind, !!retry),
    closeLabel: closeLabel(awaiting, !!completed),
    add: () => open({ kind: VoiceDialogAction.Create }),
    setName: (event: ChangeEvent<HTMLInputElement>) => setName(event.target.value),
    setInput: (event: ChangeEvent<HTMLSelectElement>) => setInput(event.target.value),
    submit: () => void submit(),
    close: () => void close(),
    onDialogCancel: (event: SyntheticEvent<HTMLDialogElement>) => {
      event.preventDefault();
      void close();
    },
  };
}

export type VoiceProfilesView = ReturnType<typeof useVoiceProfiles>;
