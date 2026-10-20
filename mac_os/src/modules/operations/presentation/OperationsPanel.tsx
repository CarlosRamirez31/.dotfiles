import { useEffect, useState } from 'react';
import type { OperationsPort } from '../application/operations-port';
import type { Operation, OperationStatus } from '../domain/operation';

const labels: Record<OperationStatus, string> = {
  accepted: 'En cola',
  running: 'En curso',
  cancellation_requested: 'Cancelación solicitada',
  succeeded: 'Completado',
  failed: 'No se pudo completar',
  cancelled: 'Cancelado',
  interrupted: 'Interrumpido al cerrar el servicio',
};

export function OperationsPanel({ operations }: { operations: OperationsPort }) {
  const [items, setItems] = useState<Operation[]>([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [retryKey, setRetryKey] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    const update = (operation: Operation) =>
      setItems((current) =>
        [operation, ...current.filter((item) => item.operationId !== operation.operationId)].slice(0, 100),
      );
    void (async () => {
      try {
        const recent = await operations.recent(controller.signal);
        if (controller.signal.aborted) return;
        if (!recent.ok) {
          setError(recent.error.message);
          return;
        }
        setItems(recent.value);
        await operations.subscribe((event) => update(event.operation), setConnected, controller.signal);
      } catch {
        if (!controller.signal.aborted)
          setError('No se pudo recuperar el historial. Cierra y vuelve a abrir la app.');
      }
    })();
    return () => controller.abort();
  }, [operations]);

  async function check() {
    setBusy(true);
    setError('');
    const key = retryKey ?? crypto.randomUUID();
    setRetryKey(key);
    try {
      const result = await operations.checkStorage(key);
      if (!result.ok) {
        setError(result.error.message);
        return;
      }
      setRetryKey(null);
      // SSE owns status updates; a late HTTP response must not overwrite a completed event.
    } catch (error) {
      setError(error instanceof Error ? error.message : 'No se pudo iniciar. Puedes reintentar.');
    } finally {
      setBusy(false);
    }
  }
  async function cancel(id: string) {
    try {
      const result = await operations.cancel(id);
      if (!result.ok) setError(result.error.message);
    } catch {
      setError('No se pudo solicitar la cancelación.');
    }
  }
  return (
    <section>
      <h2>Operaciones locales</h2>
      <p role="status">{connected ? 'Servicio conectado' : 'Conectando con el servicio…'}</p>
      <p>Comprueba la integridad de la base cifrada. No captura audio ni ejecuta modelos de IA.</p>
      <button disabled={busy || !connected} onClick={() => void check()}>
        {retryKey ? 'Reintentar diagnóstico' : 'Verificar almacenamiento'}
      </button>
      {error && <p role="alert">{error}</p>}
      {items.length === 0 && <p>No hay diagnósticos registrados.</p>}
      <ul>
        {items.map((item) => (
          <li key={item.operationId}>
            <strong>
              {item.kind === 'audio.start'
                ? 'Filtro de audio'
                : item.kind === 'personal_voice.enroll'
                  ? 'Registro de voz'
                  : 'Diagnóstico'}
              : {labels[item.status]}
            </strong>
            {item.detail && (
              <p>{details[item.detail] ?? 'Consulta la documentación de desarrollo para este resultado.'}</p>
            )}{' '}
            <small>{item.operationId}</small>
            {['accepted', 'running'].includes(item.status) && (
              <button onClick={() => void cancel(item.operationId)}>Cancelar</button>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}

const details: Record<string, string> = {
  preparing_voice_model: 'Preparando el modelo local de voz…',
  recording_enrollment_10_seconds: 'Habla durante 10 segundos con tu voz normal.',
  creating_voice_profile: 'Creando tu perfil de voz…',
  voice_enrolled: 'Perfil de voz guardado y cifrado.',
  audio_active: 'Capturando y enviando audio filtrado a BlackHole.',
  audio_stopped: 'Captura detenida.',
  integrity_ok: 'La integridad del almacenamiento es correcta.',
  personal_voice_runtime_not_installed: 'Falta instalar el runtime privado de voz personal.',
  voice_enrollment_required: 'Registra tu voz antes de iniciar el filtro personal.',
  blackhole_2ch_not_installed: 'BlackHole 2ch no está instalado.',
  requires_float32_48khz_mono_or_stereo: 'Este prototipo requiere 48 kHz, float32 y uno o dos canales.',
  audio_device_or_format_unavailable: 'No se pudo abrir el dispositivo o su formato.',
  audio_overrun_or_device_lost: 'Se detuvo por sobrecarga o pérdida del dispositivo.',
  audio_output_backpressure: 'Se detuvo porque la salida no consumía el audio a tiempo.',
  microphone_timeout_or_permission_denied: 'No llegó audio. Revisa los permisos de micrófono.',
  personal_voice_model_load_failed: 'No se pudo cargar el modelo local.',
  noise_processing_failed: 'Falló el procesamiento de reducción de ruido.',
  personal_voice_inference_failed: 'Falló el procesamiento de voz personal.',
  personal_voice_timeout: 'El modelo no respondió a tiempo; se detuvo la sesión.',
  enrollment_too_quiet: 'El registro fue demasiado silencioso. Acércate al micrófono y repite.',
  service_restarted: 'El servicio se reinició. La captura no se reanuda automáticamente.',
};
