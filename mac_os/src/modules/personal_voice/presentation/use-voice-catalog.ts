import { useEffect, useState } from 'react';
import type { VoiceProfilesPort } from '../application/voice-profiles-port';
import type { VoiceProfile } from '../domain/voice-profile';
import { selectedVoice } from '../application/profile-selection';

export function useVoiceCatalog(
  profiles: VoiceProfilesPort,
  revision: string,
  onError: (message: string) => void,
) {
  const [rows, setRows] = useState<VoiceProfile[]>([]);
  const [selected, setSelected] = useState('');
  const [loading, setLoading] = useState(true);
  const [refreshCount, setRefreshCount] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    void profiles.list(controller.signal).then((result) => {
      if (controller.signal.aborted) return;
      setLoading(false);
      if (!result.ok) {
        onError(result.error.message);
        return;
      }
      setRows(result.value);
      setSelected((current) => selectedVoice(result.value, current));
    });
    return () => controller.abort();
  }, [profiles, revision, refreshCount, onError]);
  return { rows, selected, setSelected, loading, refresh: () => setRefreshCount((value) => value + 1) };
}
