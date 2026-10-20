import { localConnection } from '../commons/connection.ts';
import { clientOptions } from '../commons/options';
import { logClient } from './logging';
import { invoke } from '@tauri-apps/api/core';
import { HttpOperations } from '../modules/operations/infrastructure/http-operations';
import { HttpVoiceProfiles } from '../modules/personal_voice/infrastructure/http-voice-profiles';
import type { VoiceProfilesPort } from '../modules/personal_voice/application/voice-profiles-port';
import { HttpAudio } from '../modules/audio/infrastructure/http-audio';
import { createHttp } from '../commons/http';
import type { OperationsPort } from '../modules/operations/application/operations-port';
import type { AudioPort } from '../modules/audio/application/audio-port';

export interface Services {
  operations: OperationsPort;
  audio: AudioPort;
  voices: VoiceProfilesPort;
}
export async function createServices(): Promise<Services> {
  const connection = localConnection(await invoke<unknown>('local_connection'));
  const options = clientOptions(await invoke<unknown>('public_options'));
  const http = createHttp(connection, logClient);
  return {
    operations: new HttpOperations(http, logClient, options),
    audio: new HttpAudio(http),
    voices: new HttpVoiceProfiles(http),
  };
}
