import { useNativeDialog } from '../../../commons/use-native-dialog';
import { useVoiceProfiles, type VoiceProfilesProps } from './use-voice-profiles';
export function VoiceProfilesPanel(props: VoiceProfilesProps) {
  const view = useVoiceProfiles(props);
  const dialogRef = useNativeDialog(view.modalOpen);
  return (
    <section aria-labelledby="voices-title">
      <h2 id="voices-title">Mis voces</h2>
      <p>La voz predeterminada queda seleccionada al abrir la app. La captura se inicia por separado.</p>
      {view.loading && <p role="status">Cargando voces…</p>}
      {view.active && <p role="status">Detén la captura o el registro antes de modificar tus voces.</p>}
      {!view.loading && view.rows.length === 0 && (
        <p>No tienes voces registradas. Puedes usar reducción de ruido sin voz personal.</p>
      )}
      <ul>
        {view.rows.map((profile) => (
          <li key={profile.id}>
            <label>
              <input
                type="radio"
                name="voice-selection"
                checked={profile.selected}
                disabled={view.active || view.busy}
                onChange={profile.select}
              />
              {profile.label}
            </label>{' '}
            {!profile.isDefault && (
              <button disabled={view.active || view.busy} onClick={profile.makeDefault}>
                Usar por defecto
              </button>
            )}{' '}
            <button disabled={view.active || view.busy} onClick={profile.edit}>
              Editar / reemplazar {profile.name}
            </button>{' '}
            <button disabled={view.active || view.busy} onClick={profile.delete}>
              Eliminar {profile.name}
            </button>
          </li>
        ))}
      </ul>
      <button disabled={view.active || view.busy || view.loading} onClick={view.add}>
        Agregar voz
      </button>
      {view.message && !view.modal && <p role="status">{view.message}</p>}
      <dialog ref={dialogRef} aria-labelledby="voice-dialog-title" onCancel={view.onDialogCancel}>
        <h2 id="voice-dialog-title">{view.title}</h2>
        {view.deleting && (
          <>
            <p>
              Eliminar «{view.modal && 'profile' in view.modal && view.modal.profile.name}» de esta aplicación
              no se puede deshacer. Deberás registrarla de nuevo para volver a usarla.
            </p>
            {view.deleteBlocked && <p role="alert">Primero elige otra voz como predeterminada.</p>}
          </>
        )}
        {!view.deleting && (
          <>
            <p>
              Se capturan 10 segundos con tu consentimiento. El audio se procesa en memoria; se guarda un
              perfil cifrado, no la grabación. La detección personal es experimental y puede dejar pasar otras
              voces.
            </p>
            {view.replacing && (
              <p>
                La voz anterior se conserva hasta que termine correctamente el nuevo registro. Cancelar o
                fallar no la reemplaza.
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
        {!view.pendingId && (
          <button disabled={view.confirmDisabled} onClick={view.submit}>
            {view.submitLabel}
          </button>
        )}{' '}
        <button disabled={view.busy} onClick={view.close}>
          {view.closeLabel}
        </button>
      </dialog>
    </section>
  );
}
