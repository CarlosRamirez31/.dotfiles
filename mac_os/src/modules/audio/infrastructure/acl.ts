import { InvalidResponseError } from '../../../commons/errors.ts';
import type { AudioDevices } from '../application/audio-port.ts';

export function audioDevices(value: unknown): AudioDevices {
  if (
    !value ||
    typeof value !== 'object' ||
    !('inputs' in value) ||
    !Array.isArray(value.inputs) ||
    !('blackholeAvailable' in value) ||
    typeof value.blackholeAvailable !== 'boolean' ||
    value.inputs.some((x) => !x || typeof x.id !== 'string' || typeof x.name !== 'string')
  )
    throw new InvalidResponseError();
  return {
    inputs: value.inputs.map((x) => ({ id: x.id, name: x.name })),
    blackholeAvailable: value.blackholeAvailable,
  };
}
