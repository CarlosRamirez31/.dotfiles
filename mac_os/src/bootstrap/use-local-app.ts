import { useEffect, useState } from 'react';
import { logClient } from './logging';
import { createServices, type Services } from './operations';
import type { Operation } from '../modules/operations/domain/operation';
export function useLocalApp() {
  const [services, setServices] = useState<Services | null>(null);
  const [selectedVoice, setSelectedVoice] = useState('');
  const [items, setItems] = useState<Operation[]>([]);
  const [error, setError] = useState(false);
  useEffect(() => {
    let active = true;
    void createServices()
      .then((port) => {
        if (active) setServices(port);
      })
      .catch(() => {
        if (active) {
          setError(true);
          logClient('startup_failed');
        }
      });
    return () => {
      active = false;
    };
  }, []);
  return { services, selectedVoice, items, setSelectedVoice, setItems, error, loading: !services && !error };
}
