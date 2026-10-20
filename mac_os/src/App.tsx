import { logClient } from './bootstrap/logging';
import { useEffect, useState } from 'react';
import { createServices, type Services } from './bootstrap/operations';
import { AudioPanel } from './modules/audio/presentation/AudioPanel';
import { OperationsPanel } from './modules/operations/presentation/OperationsPanel';

function App() {
  const [operations, setOperations] = useState<Services | null>(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    let active = true;
    void createServices()
      .then((port) => {
        if (active) setOperations(port);
      })
      .catch(() => {
        if (active) {
          setError(true);
          logClient('startup_failed');
        }
      });
    return () => {
      active = false;
    };
  }, []);
  return (
    <main>
      <h1>mac_os · Local</h1>
      {error ? (
        <p role="alert">Servicio local no disponible. Abre la aplicación con Tauri y vuelve a intentarlo.</p>
      ) : operations ? (
        <>
          <AudioPanel audio={operations.audio} />
          <OperationsPanel operations={operations.operations} />
        </>
      ) : (
        <p role="status">Preparando servicio local…</p>
      )}
    </main>
  );
}
export default App;
