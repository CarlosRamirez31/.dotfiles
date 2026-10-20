import {
  OperationStatus,
  OperationKind,
  OperationDetail,
  canCancel,
  type Operation,
} from '../domain/operation.ts';
const statusLabels: Record<OperationStatus, string> = {
  [OperationStatus.Accepted]: 'En cola',
  [OperationStatus.Running]: 'En curso',
  [OperationStatus.CancellationRequested]: 'Cancelación solicitada',
  [OperationStatus.Succeeded]: 'Completado',
  [OperationStatus.Failed]: 'No se pudo completar',
  [OperationStatus.Cancelled]: 'Cancelado',
  [OperationStatus.Interrupted]: 'Interrumpido al cerrar el servicio',
};
const kindLabels: Record<OperationKind, string> = {
  [OperationKind.AudioStart]: 'Filtro de audio',
  [OperationKind.VoiceEnrollment]: 'Registro de voz',
  [OperationKind.StorageCheck]: 'Diagnóstico',
};
const detailMessages: Record<OperationDetail, string> = {
  [OperationDetail.PreparingVoiceModel]: 'Preparando el modelo local de voz…',
  [OperationDetail.RecordingEnrollment10Seconds]: 'Habla durante 10 segundos con tu voz normal.',
  [OperationDetail.CreatingVoiceProfile]: 'Creando tu perfil de voz…',
  [OperationDetail.VoiceEnrolled]: 'Perfil de voz guardado y cifrado.',
  [OperationDetail.VoiceProfileCapacity]: 'Se alcanzó el máximo de perfiles de voz configurado.',
  [OperationDetail.VoiceSelectionRequired]: 'Selecciona el perfil de voz que quieres reemplazar.',
  [OperationDetail.AudioActive]: 'Capturando y enviando audio filtrado a BlackHole.',
  [OperationDetail.AudioStopped]: 'Captura detenida.',
  [OperationDetail.IntegrityOk]: 'La integridad del almacenamiento es correcta.',
  [OperationDetail.PersonalVoiceRuntimeNotInstalled]: 'Falta instalar el runtime privado de voz personal.',
  [OperationDetail.VoiceEnrollmentRequired]: 'Registra tu voz antes de iniciar el filtro personal.',
  [OperationDetail.Blackhole2chNotInstalled]: 'BlackHole 2ch no está instalado.',
  [OperationDetail.RequiresFloat3248khzMonoOrStereo]:
    'Este prototipo requiere 48 kHz, float32 y uno o dos canales.',
  [OperationDetail.AudioDeviceOrFormatUnavailable]: 'No se pudo abrir el dispositivo o su formato.',
  [OperationDetail.AudioOverrunOrDeviceLost]: 'Se detuvo por sobrecarga o pérdida del dispositivo.',
  [OperationDetail.AudioOutputBackpressure]: 'Se detuvo porque la salida no consumía el audio a tiempo.',
  [OperationDetail.MicrophoneTimeoutOrPermissionDenied]: 'No llegó audio. Revisa los permisos de micrófono.',
  [OperationDetail.PersonalVoiceModelLoadFailed]: 'No se pudo cargar el modelo local.',
  [OperationDetail.NoiseProcessingFailed]: 'Falló el procesamiento de reducción de ruido.',
  [OperationDetail.PersonalVoiceInferenceFailed]: 'Falló el procesamiento de voz personal.',
  [OperationDetail.PersonalVoiceTimeout]: 'El modelo no respondió a tiempo; se detuvo la sesión.',
  [OperationDetail.EnrollmentTooQuiet]:
    'El registro fue demasiado silencioso. Acércate al micrófono y repite.',
  [OperationDetail.ServiceRestarted]: 'El servicio se reinició. La captura no se reanuda automáticamente.',
};
export function operationView(item: Operation) {
  let detail = '';
  if (item.detail)
    detail =
      detailMessages[item.detail as OperationDetail] ??
      'Consulta la documentación de desarrollo para este resultado.';
  return {
    id: item.operationId,
    title: kindLabels[item.kind],
    status: statusLabels[item.status],
    detail,
    canCancel: canCancel(item.status),
  };
}
