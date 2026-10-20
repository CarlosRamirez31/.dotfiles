import { useAudioPanel, type AudioPanelProps } from './use-audio-panel';
export function AudioPanel(props: AudioPanelProps) {
  const view = useAudioPanel(props);
  return (
    <section>
      <h2>Micrófono local · experimental</h2>
      <p>
        Elige BlackHole 2ch como entrada en tu aplicación de llamadas. La captura comienza solo al pulsar
        Iniciar.
      </p>
      {view.missingBlackHole && (
        <p role="status">
          Falta BlackHole 2ch. Instálalo por separado y vuelve a abrir la app para usar la salida filtrada.
        </p>
      )}
      <label>
        Micrófono{' '}
        <select value={view.input} disabled={view.fieldsDisabled} onChange={view.onInput}>
          {view.devices.map((device) => (
            <option key={device.id} value={device.id}>
              {device.name}
            </option>
          ))}
        </select>
      </label>
      <label>
        <input
          type="checkbox"
          checked={view.personal}
          disabled={view.fieldsDisabled}
          onChange={view.onPersonal}
        />
        Filtrar por mi voz (requiere registro)
      </label>
      <button disabled={view.startDisabled} onClick={view.start}>
        {view.label}
      </button>
      <p>
        Voz personal puede rechazar tu voz o dejar pasar otras, especialmente si hablan al mismo tiempo. No
        garantiza aislamiento del hablante.
      </p>
      {view.message && <p role="status">{view.message}</p>}
    </section>
  );
}
