import { VoiceProfileDialog } from './VoiceProfileDialog';
import { useVoiceProfiles, type VoiceProfilesProps } from './use-voice-profiles';
export function VoiceProfilesPanel(props: VoiceProfilesProps) {
  const view = useVoiceProfiles(props);
  return (
    <section aria-labelledby="voices-title">
      <h2 id="voices-title">Mis voces</h2>
      <p>La voz predeterminada queda seleccionada al abrir la app. La captura se inicia por separado.</p>
      {view.loading && <p role="status">Cargando voces…</p>}
      {view.active && <p role="status">Detén la captura o el registro antes de modificar tus voces.</p>}
      {view.empty && <p>No tienes voces registradas. Puedes usar reducción de ruido sin voz personal.</p>}
      <ul>
        {view.rows.map((profile) => (
          <li key={profile.id}>
            <label>
              <input
                type="radio"
                name="voice-selection"
                checked={profile.selected}
                disabled={view.managementDisabled}
                onChange={profile.select}
              />
              {profile.label}
            </label>{' '}
            {profile.canMakeDefault && (
              <button disabled={view.managementDisabled} onClick={profile.makeDefault}>
                Usar por defecto
              </button>
            )}{' '}
            <button disabled={view.managementDisabled} onClick={profile.edit}>
              Editar / reemplazar {profile.name}
            </button>{' '}
            <button disabled={view.managementDisabled} onClick={profile.delete}>
              Eliminar {profile.name}
            </button>
          </li>
        ))}
      </ul>
      <button disabled={view.addDisabled} onClick={view.add}>
        Agregar voz
      </button>
      {view.outsideMessage && <p role="status">{view.outsideMessage}</p>}
      <VoiceProfileDialog view={view} />
    </section>
  );
}
