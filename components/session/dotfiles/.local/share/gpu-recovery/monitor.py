#!/usr/bin/env python3
"""Recover the verified LOQ 15AHP9 GPE10 loop after external-monitor unplug."""
import argparse
import logging
import os
from pathlib import Path
import re
import signal
import time

LOG = logging.getLogger('gpu-recovery')


class Hardware:
    def __init__(self, root=Path('/sys'), runtime=Path('/run/dotfiles-gpu-recovery')):
        self.root = root
        self.gpu = root / 'bus/pci/devices/0000:01:00.0'
        self.gpe = root / 'firmware/acpi/interrupts/gpe10'
        self.marker = runtime / 'gpe10-disabled'

    def validate(self):
        model = (self.root / 'class/dmi/id/product_version').read_text().strip()
        vendor = (self.gpu / 'vendor').read_text().strip()
        device = (self.gpu / 'device').read_text().strip()
        parent = (self.gpu.resolve().parent / 'firmware_node/path').read_text().strip()
        if (model != 'LOQ 15AHP9' or vendor != '0x10de' or device != '0x28e1'
                or not parent.endswith('.GPP0')):
            raise RuntimeError('El equipo no coincide con el hardware validado para GPE10.')

    def connectors(self):
        connected = active = False
        paths = list((self.root / 'class/drm').glob('card*-*/status'))
        if not paths:
            raise RuntimeError('No hay estados de conectores DRM accesibles.')
        for path in paths:
            if re.match(r'card\d+-(eDP|LVDS|DSI|Writeback)', path.parent.name):
                continue
            status = path.read_text().strip()
            if status not in ('connected', 'disconnected'):
                raise RuntimeError(f'Estado de conector desconocido: {path.parent.name}')
            connected |= status == 'connected'
            active |= (path.parent / 'enabled').read_text().strip() == 'enabled'
        return connected, active

    def sample(self):
        connected, active = self.connectors()
        power = self.gpu / 'power'
        return dict(connected=connected, ready=not active,
                    active=int((power / 'runtime_active_time').read_text()),
                    suspended=int((power / 'runtime_suspended_time').read_text()),
                    gpe=int(self.gpe.read_text().split()[0]))

    def restore(self):
        if self.marker.exists():
            if 'enabled' not in self.gpe.read_text().split():
                self.gpe.write_text('enable\n')
            if 'enabled' not in self.gpe.read_text().split():
                raise RuntimeError('No se confirmó la restauración de GPE10.')
            self.marker.unlink()
            LOG.info('GPE10 restaurado y habilitado.')

    def recover(self, sleep=time.sleep):
        state = self.gpe.read_text().split()
        if 'enabled' not in state or 'unmasked' not in state:
            LOG.warning('Se conserva GPE10: ya estaba deshabilitado o enmascarado.')
            return
        if self.connectors() != (False, False):
            return
        LOG.info('Ciclo de reactivaciones detectado; recuperación temporal de GPE10.')
        # A marker lets ExecStopPost restore the event even after a forced kill.
        self.marker.parent.mkdir(parents=True, exist_ok=True)
        self.marker.write_text('restore enable\n')
        try:
            self.gpe.write_text('disable\n')
            if 'disabled' not in self.gpe.read_text().split():
                raise RuntimeError('No se confirmó la desactivación temporal de GPE10.')
            for _ in range(15):
                sleep(1)
                if self.connectors() != (False, False):
                    LOG.info('Cambió la conexión de pantallas; terminando la recuperación.')
                    break
        finally:
            self.restore()
        LOG.info('Recuperación terminada; estado RTX: %s',
                 (self.gpu / 'power/runtime_status').read_text().strip())


class Detector:
    """One assessment per disconnect/start, with a 10s grace and 20s window."""
    def __init__(self):
        self.connected = None
        self.due = None
        self.baseline = None
        self.last_attempt = float('-inf')

    def update(self, now, sample):
        if sample['connected'] != self.connected:
            self.connected = sample['connected']
            self.baseline = None
            self.due = None if self.connected else max(now + 10, self.last_attempt + 60)
            LOG.info('Monitores externos: %s.', 'conectados' if self.connected else 'desconectados')
        if self.due is None or now < self.due or not sample['ready']:
            return False
        if self.baseline is None:
            self.baseline = (now, sample.copy())
            return False
        then, before = self.baseline
        if now - then < 20:
            return False
        self.due = None
        active = sample['active'] - before['active']
        suspended = sample['suspended'] - before['suspended']
        events = sample['gpe'] - before['gpe']
        cycle = active > 0 and suspended > 0 and events >= 2 and active > suspended
        LOG.info('Comprobación: activa=%d ms, suspendida=%d ms, GPE10 nuevos=%d; ciclo=%s.',
                 active, suspended, events, cycle)
        if cycle:
            self.last_attempt = now
        return cycle


def stop(signum, frame):
    raise KeyboardInterrupt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--restore', action='store_true')
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    hardware = Hardware()
    hardware.validate()
    if args.check:
        print('Hardware compatible:', hardware.sample())
        return
    if os.geteuid() != 0:
        raise SystemExit('Este servicio requiere root.')
    if args.restore:
        hardware.restore()
        return
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(sig, stop)
    hardware.restore()
    detector = Detector()
    try:
        while True:
            sample = hardware.sample()
            if detector.update(time.monotonic(), sample):
                hardware.recover()
            time.sleep(2)
    except KeyboardInterrupt:
        LOG.info('Servicio detenido.')
    finally:
        hardware.restore()


if __name__ == '__main__':
    main()
