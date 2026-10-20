import { useEffect, useState, type ChangeEvent, type SyntheticEvent } from 'react';
import type { VoiceProfilesPort, VoiceEnrollment } from '../application/voice-profiles-port';
import type { VoiceProfile } from '../domain/voice-profile';
import { OperationKind, isTerminal, type Operation } from '../../operations/domain/operation.ts';
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
  const [loading, setLoading] = useState(true);
  const [rows, setRows] = useState<VoiceProfile[]>([]);
  const [selected, setSelected] = useState('');
  const [modal, setModal] = useState<VoiceDialog | null>(null);
  const [name, setName] = useState('');
  const [input, setInput] = useState('');
  const [inputs, setInputs] = useState<{ id: string; name: string }[]>([]);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [retry, setRetry] = useState<VoiceEnrollment | null>(null);
  const [pendingId, setPendingId] = useState('');
  const [refresh, setRefresh] = useState(0);
  const revision = items
    .filter((item) => item.kind === OperationKind.VoiceEnrollment)
    .map((item) => `${item.operationId}:${item.status}`)
    .join('|');
  const active = items.some((item) => item.kind !== OperationKind.StorageCheck && !isTerminal(item.status));
  const pending = items.find((item) => item.operationId === pendingId);
  useEffect(() => {
    onSelect(selected);
  }, [selected, onSelect]);
  useEffect(() => {
    const controller = new AbortController();
    void profiles.list(controller.signal).then((result) => {
      if (controller.signal.aborted) return;
      if (!result.ok) {
        setLoading(false);
        setMessage(result.error.message);
        return;
      }
      setLoading(false);
      setRows(result.value);
      setSelected((current) =>
        result.value.some((p) => p.id === current)
          ? current
          : (result.value.find((p) => p.isDefault)?.id ?? ''),
      );
    });
    return () => controller.abort();
  }, [profiles, revision, refresh]);
  useEffect(() => {
    const controller = new AbortController();
    void audio.devices(controller.signal).then((result) => {
      if (controller.signal.aborted || !result.ok) return;
      setInputs(result.value.inputs);
      setInput(result.value.inputs[0]?.id ?? '');
    });
    return () => controller.abort();
  }, [audio]);
  function open(value: VoiceDialog) {
    setMessage('');
    setName(value.kind === VoiceDialogAction.Create ? '' : value.profile.name);
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
      setRefresh((value) => value + 1);
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
        setRefresh((value) => value + 1);
        setMessage('Voz eliminada de la aplicación.');
      } else setMessage(result.error.message);
    } else {
      const request = retry ?? {
        inputId: input,
        profileId: modal.kind === VoiceDialogAction.Create ? crypto.randomUUID() : modal.profile.id,
        name: name.trim(),
        replace: modal.kind === VoiceDialogAction.Replace,
        key: crypto.randomUUID(),
      };
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
  const deleteBlocked = deleting && modal.profile.isDefault && rows.length > 1;
  let confirmDisabled = busy || active || loading;
  if (deleting) confirmDisabled ||= deleteBlocked;
  else confirmDisabled ||= !input || !name.trim();
  const fieldsDisabled = busy || awaiting || !!retry || !!completed;
  const viewRows = rows.map((profile) => ({
    ...profile,
    selected: selected === profile.id,
    label: profile.name + (profile.isDefault ? ' · Predeterminada' : ''),
    select: () => setSelected(profile.id),
    makeDefault: () => void makeDefault(profile.id),
    edit: () => open({ kind: VoiceDialogAction.Replace, profile }),
    delete: () => open({ kind: VoiceDialogAction.Delete, profile }),
  }));
  return {
    rows: viewRows,
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
