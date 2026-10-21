#!/usr/bin/env python3
"""Guided terminal display for the direct voice probe."""
import runpy
import shutil
import sys
import textwrap
import time
from pathlib import Path


class Screen:
    def __init__(self):
        self.tty = sys.stdout.isatty()
        self.width = min(84, max(36, shutil.get_terminal_size((80, 24)).columns - 2))
        self.stage = 0
        self.passage = ''
        self.instruction = ''
        self.elapsed = 0
        self.seconds = 10

    def show(self, state, footer='', remaining=None):
        width = self.width - 4
        lines = ['PRUEBA DE VOZ  /  SOLO MI VOZ', '']
        if self.stage:
            title = ('TU VOZ', 'OTRA PERSONA', 'SILENCIO')[self.stage - 1]
            lines += [f'ETAPA {self.stage}/3  ·  {title}', self.instruction, '', state]
            if remaining is not None:
                lines += [f'Empieza en {remaining} segundos. Todos en silencio.']
            else:
                filled = round(24 * self.elapsed / self.seconds)
                lines += [f'[{"━" * filled}{"·" * (24 - filled)}]  {self.elapsed:02d} / {self.seconds:02d} s']
            lines += ['', 'TEXTO PARA LEER' if self.passage else 'DURANTE ESTA ETAPA',
                      self.passage or 'Ambos permanezcan callados hasta que termine el contador.']
        else:
            lines += [state, '', '1. Tu voz: 10 segundos', '2. Otra persona: 10 segundos',
                      '3. Silencio: 5 segundos', '',
                      'Confirma cada etapa con Enter. Tendrás 5 segundos para prepararte.',
                      'Lee el texto seguido hasta que termine el tiempo.', '',
                      'El audio se mide y se descarta. No se guarda ninguna grabación.']
        lines += ['', footer, 'Ctrl+C para salir']
        wrapped = []
        for line in lines:
            wrapped.extend(textwrap.wrap(line, width, break_long_words=True) or [''])
        border = '─' * (self.width - 2)
        content = ['┌' + border + '┐']
        content += ['│ ' + line.ljust(width) + ' │' for line in wrapped]
        content += ['└' + border + '┘']
        prefix = '\033[H\033[J\033[36m' if self.tty else ''
        suffix = '\033[0m' if self.tty else ''
        print(prefix + '\n'.join(content) + suffix, flush=True)

    def confirm(self):
        if self.tty:
            print('\033[?25h', end='', flush=True)
        try:
            input('  Pulsa Enter cuando estén listos: ')
        finally:
            if self.tty:
                print('\033[?25l', end='', flush=True)

    def prepare(self, instruction, passage, seconds):
        self.stage += 1
        self.instruction = instruction
        self.passage = passage or ''
        self.seconds = seconds
        self.elapsed = 0
        self.show('PREPARACIÓN', 'Lee las instrucciones y confirma con Enter.')
        self.confirm()
        for remaining in range(5, 0, -1):
            self.show('PREPÁRATE', 'Todavía no hablen.', remaining=remaining)
            time.sleep(1)
        self.show('SILENCIO AHORA' if self.stage == 3 else 'LEE AHORA',
                  'Continúa hasta que termine el contador.')

    def progress(self, second, rms):
        self.elapsed = second
        meter = min(16, round(rms * 160))
        self.show('ETAPA COMPLETADA' if second == self.seconds else
                  ('SILENCIO AHORA' if self.stage == 3 else 'LEE AHORA'),
                  ('Puedes dejar de leer. ' if second == self.seconds else '') +
                  f'Audio hacia las aplicaciones: [{"■" * meter}{"·" * (16 - meter)}]')


def main():
    screen = Screen()
    if '--preview' in sys.argv:
        screen.stage = 1
        screen.instruction = 'Lee tú. La otra persona debe permanecer callada.'
        screen.passage = ('Esta mañana abrí la ventana y miré las nubes mientras preparaba un café. '
                          'Después busqué mi cuaderno y organicé las cosas sobre la mesa. '
                          'Estoy leyendo a mi ritmo normal, sin gritar ni cambiar mi voz, '
                          'como cuando converso con alguien de confianza. '
                          'Sigo leyendo tranquilamente hasta que termine el contador.')
        screen.show('PREPÁRATE', 'Todavía no hablen.', remaining=5)
        return 0
    try:
        if screen.tty:
            print('\033[?1049h\033[?25l', end='', flush=True)
        screen.show('ANTES DE EMPEZAR', 'Pulsa Enter para conectar el micrófono.')
        screen.confirm()
        screen.show('CONECTANDO EL MICRÓFONO…', 'Espera mientras se activa el modelo.')
        runpy.run_path(str(Path(__file__).resolve().with_name('dotfiles-voice-probe')),
                       init_globals={'screen': screen}, run_name='voice_probe')
    except (KeyboardInterrupt, EOFError):
        message = 'Prueba cancelada. El micrófono de prueba se cerró.'
        code = 130
    except (OSError, ValueError, RuntimeError) as error:
        message = f'No se completó la prueba: {error}'
        code = 1
    else:
        message = 'Prueba completada. Puedes dejar de hablar.'
        code = 0
    finally:
        if screen.tty:
            print('\033[?25h\033[?1049l', end='', flush=True)
    print(message)
    print('Diagnóstico: /tmp/solo-mi-voz-prueba.jsonl')
    return code


if __name__ == '__main__':
    sys.exit(main())
