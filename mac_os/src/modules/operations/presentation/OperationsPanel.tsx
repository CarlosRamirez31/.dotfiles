import { useOperationsPanel, type OperationsPanelProps } from './use-operations-panel';
export function OperationsPanel(props: OperationsPanelProps) {
  const view = useOperationsPanel(props);
  return (
    <section>
      <h2>Operaciones locales</h2>
      <p role="status">{view.connectionMessage}</p>
      <p>Comprueba la integridad de la base cifrada. No captura audio ni ejecuta modelos de IA.</p>
      <button disabled={view.checkDisabled} onClick={view.check}>
        {view.checkLabel}
      </button>
      {view.error && <p role="alert">{view.error}</p>}
      {view.rows.length === 0 && <p>No hay operaciones registradas.</p>}
      <ul>
        {view.rows.map((item) => (
          <li key={item.id}>
            <strong>
              {item.title}: {item.status}
            </strong>
            {item.detail && <p>{item.detail}</p>} <small>{item.id}</small>
            {item.canCancel && <button onClick={item.cancel}>Cancelar</button>}
          </li>
        ))}
      </ul>
    </section>
  );
}
