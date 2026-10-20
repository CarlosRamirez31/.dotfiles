import { useAudioInputs } from './use-audio-inputs';
import { useState, type ChangeEvent } from 'react';
import { AppErrorCode } from '../../../commons/errors.ts';
import type { AudioPort } from '../application/audio-port';
export interface AudioPanelProps {
  audio: AudioPort;
  voiceProfileId: string;
}
interface AudioRequest {
  key: string;
  input: string;
  personal: boolean;
  voiceId: string;
}
export function useAudioPanel({ audio, voiceProfileId }: AudioPanelProps) {
  const [personal, setPersonal] = useState(false);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [pending, setPending] = useState<AudioRequest | null>(null);
  const { devices, input, setInput } = useAudioInputs(audio, setMessage);
  async function submit() {
    if (personal && !voiceProfileId) {
      setMessage('Selecciona una voz registrada.');
      return;
    }
    const request = pending ?? { key: crypto.randomUUID(), input, personal, voiceId: voiceProfileId };
    setPending(request);
    setBusy(true);
    try {
      const result = await audio.start(request.input, request.personal, request.key, request.voiceId);
      if (!result.ok) {
        setMessage(result.error.message);
        if (result.error.code === AppErrorCode.Rejected) setPending(null);
        return;
      }
      setPending(null);
      setMessage('Solicitud aceptada. Consulta el progreso debajo; puedes detenerla desde su operación.');
    } catch {
      setMessage('No se pudo enviar. Reintenta la misma solicitud.');
    } finally {
      setBusy(false);
    }
  }
  let label = 'Iniciar filtro';
  if (pending) label = 'Reintentar inicio';
  return {
    devices: devices?.inputs ?? [],
    missingBlackHole: devices && !devices.blackholeAvailable,
    input,
    personal,
    message,
    fieldsDisabled: busy || !!pending,
    startDisabled: !input || busy || !devices?.blackholeAvailable || (personal && !voiceProfileId),
    label,
    onInput: (event: ChangeEvent<HTMLSelectElement>) => setInput(event.target.value),
    onPersonal: (event: ChangeEvent<HTMLInputElement>) => setPersonal(event.target.checked),
    start: () => void submit(),
  };
}
