import { useEffect, useState } from 'react';
import type { AudioPort, AudioDevices } from '../application/audio-port';

export function useAudioInputs(audio: Pick<AudioPort, 'devices'>, onError?: (message: string) => void) {
  const [devices, setDevices] = useState<AudioDevices | null>(null);
  const [input, setInput] = useState('');
  useEffect(() => {
    const controller = new AbortController();
    void audio
      .devices(controller.signal)
      .then((result) => {
        if (controller.signal.aborted) return;
        if (!result.ok) {
          onError?.(result.error.message);
          return;
        }
        setDevices(result.value);
        setInput(result.value.inputs[0]?.id ?? '');
      })
      .catch(() => {
        if (!controller.signal.aborted) onError?.('No se pudieron consultar los dispositivos.');
      });
    return () => controller.abort();
  }, [audio, onError]);
  return { devices, input, setInput, inputs: devices?.inputs ?? [] };
}
