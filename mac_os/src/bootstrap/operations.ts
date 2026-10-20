import { clientOptions } from '../commons/options';
import { logClient } from './logging';
import { invoke } from '@tauri-apps/api/core';
import { HttpOperations } from '../modules/operations/infrastructure/http-operations';
import { HttpAudio } from '../modules/audio/infrastructure/http-audio';
import { createHttp, type LocalConnection } from '../commons/http';
import type { OperationsPort } from '../modules/operations/application/operations-port';
import type { AudioPort } from '../modules/audio/application/audio-port';

export interface Services {
  operations: OperationsPort;
  audio: AudioPort;
}
export async function createServices(): Promise<Services> {
  const connection = await invoke<LocalConnection>('local_connection');
  const options = clientOptions(await invoke<unknown>('public_options'));
  const http = createHttp(connection, logClient);
  return { operations: new HttpOperations(http, logClient, options), audio: new HttpAudio(http) };
}
