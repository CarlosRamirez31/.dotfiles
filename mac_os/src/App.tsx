import { useLocalApp } from './bootstrap/use-local-app';
import { VoiceProfilesPanel } from './modules/personal_voice/presentation/VoiceProfilesPanel';
import { AudioPanel } from './modules/audio/presentation/AudioPanel';
import { OperationsPanel } from './modules/operations/presentation/OperationsPanel';
export default function App() {
  const view = useLocalApp();
  return (
    <main>
      <h1>mac_os · Local</h1>
      {view.error && (
        <p role="alert">Servicio local no disponible. Abre la aplicación con Tauri y vuelve a intentarlo.</p>
      )}
      {view.loading && <p role="status">Preparando servicio local…</p>}
      {view.services && (
        <>
          <VoiceProfilesPanel
            profiles={view.services.voices}
            audio={view.services.audio}
            operations={view.services.operations}
            items={view.items}
            onSelect={view.setSelectedVoice}
          />
          <AudioPanel audio={view.services.audio} voiceProfileId={view.selectedVoice} />
          <OperationsPanel operations={view.services.operations} onChange={view.setItems} />
        </>
      )}
    </main>
  );
}
