import { useEffect, useState } from 'react';
import type { OperationsPort } from '../application/operations-port';
import type { Operation } from '../domain/operation';
import { mergeOperation } from '../application/operation-state.ts';
import { operationView } from './operation-presenter';
export interface OperationsPanelProps {
  operations: OperationsPort;
  onChange?: (items: Operation[]) => void;
}
export function useOperationsPanel({ operations, onChange }: OperationsPanelProps) {
  const [items, setItems] = useState<Operation[]>([]);
  const [lostConnection, setLostConnection] = useState(false);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [retryKey, setRetryKey] = useState<string | null>(null);

  useEffect(() => {
    onChange?.(items);
  }, [items, onChange]);
  useEffect(() => {
    const controller = new AbortController();
    const update = (operation: Operation) => setItems((current) => mergeOperation(current, operation));
    void (async () => {
      try {
        const recent = await operations.recent(controller.signal);
        if (controller.signal.aborted) return;
        if (!recent.ok) {
          setError(recent.error.message);
          return;
        }
        setItems(recent.value);
        await operations.subscribe(
          (event) => update(event.operation),
          (online) => {
            setConnected(online);
            setLostConnection(!online);
          },
          controller.signal,
        );
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
    } catch {
      setError('No se pudo iniciar. Puedes reintentar.');
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

  let connectionMessage = 'Conectando con el servicio…';
  if (connected) connectionMessage = 'Servicio conectado';
  else if (lostConnection)
    connectionMessage =
      'Servicio desconectado. Cierra y vuelve a abrir la app; la captura no se reanuda automáticamente.';
  let checkLabel = 'Verificar almacenamiento';
  if (retryKey) checkLabel = 'Reintentar diagnóstico';
  const rows = items.map((item) => ({ ...operationView(item), cancel: () => void cancel(item.operationId) }));
  return {
    rows,
    connectionMessage,
    error,
    checkLabel,
    checkDisabled: busy || !connected,
    check: () => void check(),
  };
}
