import { useEffect, useState } from 'react';
import type { AudioPort, AudioDevices } from '../application/audio-port';

export function AudioPanel({ audio }: { audio: AudioPort }) {
  const [devices, setDevices] = useState<AudioDevices | null>(null);
  const [input, setInput] = useState('');
  const [personal, setPersonal] = useState(false);
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [pending, setPending] = useState<{
    kind: 'start' | 'enroll';
    key: string;
    input: string;
    personal: boolean;
  } | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    void audio
      .devices(controller.signal)
      .then((result) => {
        setDevices(result);
        setInput(result.inputs[0]?.id ?? '');
      })
      .catch(() => {
        if (!controller.signal.aborted) setMessage('No se pudieron consultar los dispositivos.');
      });
    return () => controller.abort();
  }, [audio]);
  async function submit(kind: 'start' | 'enroll') {
    const request = pending ?? { kind, key: crypto.randomUUID(), input, personal };
    setPending(request);
    setBusy(true);
    try {
      if (request.kind === 'enroll') await audio.enroll(request.input, request.key);
      else await audio.start(request.input, request.personal, request.key);
      setPending(null);
      setMessage('Solicitud aceptada. Consulta el progreso debajo; puedes detenerla desde su operación.');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'No se pudo enviar. Reintenta la misma solicitud.');
    } finally {
      setBusy(false);
    }
  }
  return (
    <section>
      <h2>Micrófono local · experimental</h2>
      <p>
        Elige BlackHole 2ch como entrada en tu aplicación de llamadas. La captura comienza solo al pulsar
        Iniciar.
      </p>
      {devices && !devices.blackholeAvailable && (
        <p role="status">
          Falta BlackHole 2ch. Instálalo por separado y vuelve a abrir la app para usar la salida filtrada.
        </p>
      )}
      <label>
        Micrófono{' '}
        <select value={input} disabled={busy || !!pending} onChange={(event) => setInput(event.target.value)}>
          {devices?.inputs.map((device) => (
            <option key={device.id} value={device.id}>
              {device.name}
            </option>
          ))}
        </select>
      </label>
      <label>
        <input
          type="checkbox"
          checked={personal}
          disabled={busy || !!pending}
          onChange={(event) => setPersonal(event.target.checked)}
        />
        Filtrar por mi voz (requiere registro)
      </label>
      <p>
        Al registrar, espera a que aparezca «Habla durante 10 segundos». El audio se usa en memoria; se guarda
        el perfil cifrado. El registro reemplaza el perfil anterior al completarse.
      </p>
      <button
        disabled={!input || busy || (!!pending && pending.kind !== 'enroll')}
        onClick={() => void submit('enroll')}
      >
        {pending?.kind === 'enroll' ? 'Reintentar registro' : 'Registrar mi voz'}
      </button>
      <button
        disabled={!input || busy || !devices?.blackholeAvailable || (!!pending && pending.kind !== 'start')}
        onClick={() => void submit('start')}
      >
        {pending?.kind === 'start' ? 'Reintentar inicio' : 'Iniciar filtro'}
      </button>
      <p>
        Voz personal puede rechazar tu voz o dejar pasar otras, especialmente si hablan al mismo tiempo. No
        garantiza aislamiento del hablante.
      </p>
      {message && <p role="status">{message}</p>}
    </section>
  );
}
