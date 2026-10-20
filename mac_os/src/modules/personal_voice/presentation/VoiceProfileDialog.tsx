import { useNativeDialog } from '../../../commons/use-native-dialog';
import type { VoiceProfilesView } from './use-voice-profiles';
export function VoiceProfileDialog({ view }: { view: VoiceProfilesView }) {
  const dialogRef = useNativeDialog(view.modalOpen);
  return (
    <dialog ref={dialogRef} aria-labelledby="voice-dialog-title" onCancel={view.onDialogCancel}>
      <h2 id="voice-dialog-title">{view.title}</h2>
      {view.deleting && (
        <>
          <p>
            Eliminar «{view.profileName}» de esta aplicación no se puede deshacer. Deberás registrarla de
            nuevo para volver a usarla.
          </p>
          {view.deleteBlocked && <p role="alert">Primero elige otra voz como predeterminada.</p>}
        </>
      )}
      {!view.deleting && (
        <>
          <p>
            Se capturan 10 segundos con tu consentimiento. El audio se procesa en memoria; se guarda un perfil
            cifrado, no la grabación. La detección personal es experimental y puede dejar pasar otras voces.
          </p>
          {view.replacing && (
            <p>
              La voz anterior se conserva hasta que termine correctamente el nuevo registro. Cancelar o fallar
              no la reemplaza.
            </p>
          )}
          <label>
            Nombre de la voz{' '}
            <input
              value={view.name}
              maxLength={80}
              required
              disabled={view.fieldsDisabled}
              onChange={view.setName}
            />
          </label>{' '}
          <label>
            Micrófono{' '}
            <select value={view.input} disabled={view.fieldsDisabled} onChange={view.setInput}>
              {view.inputs.map((device) => (
                <option key={device.id} value={device.id}>
                  {device.name}
                </option>
              ))}
            </select>
          </label>
        </>
      )}
      {view.awaiting && <p role="status">{view.progress}</p>}
      {view.completed && <p role="status">{view.outcome}</p>}
      {view.message && <p role="alert">{view.message}</p>}
      {view.showConfirm && (
        <button disabled={view.confirmDisabled} onClick={view.submit}>
          {view.submitLabel}
        </button>
      )}{' '}
      <button disabled={view.busy} onClick={view.close}>
        {view.closeLabel}
      </button>
    </dialog>
  );
}
