import importlib.machinery
import importlib.util
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch

import gi
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import GdkPixbuf

SCRIPT = Path(__file__).resolve().parents[2] / 'bin/dotfiles-appearance'
loader = importlib.machinery.SourceFileLoader('sddm_background', str(SCRIPT))
spec = importlib.util.spec_from_loader(loader.name, loader)
app = importlib.util.module_from_spec(spec)
loader.exec_module(app)


class SddmBackground(unittest.TestCase):
    def test_reset_is_transparent_and_preserves_theme_background(self):
        image = app.sddm_background_image()
        self.assertEqual((image.get_width(), image.get_height()), (1, 1))
        self.assertEqual(bytes(image.get_pixels()), b'\0\0\0\0')

    def test_input_is_reencoded_and_scaled_without_changing_original(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'wallpaper $(literal).png'
            original = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 4000, 1000)
            original.fill(0x123456ff)
            original.savev(str(source), 'png', [], [])
            before = source.read_bytes()
            image = app.sddm_background_image(source)
            self.assertEqual((image.get_width(), image.get_height()), (3840, 960))
            self.assertEqual(source.read_bytes(), before)

    def test_nonimages_and_svg_are_rejected_before_requesting_privileges(self):
        with tempfile.TemporaryDirectory() as directory:
            for name, content in [('bad.png', 'not an image'),
                                  ('external.svg', '<svg xmlns="http://www.w3.org/2000/svg" width="2" height="2"/>')]:
                source = Path(directory) / name
                source.write_text(content)
                with self.subTest(name=name), self.assertRaises(ValueError):
                    app.sddm_background_image(source)

    def test_large_dimensions_are_rejected_before_decoding(self):
        with tempfile.NamedTemporaryFile() as source:
            fmt = GdkPixbuf.Pixbuf.get_formats()[0]
            with patch.object(GdkPixbuf.Pixbuf, 'get_file_info', return_value=(fmt, 100000, 100000)), \
                    patch.object(fmt, 'get_name', return_value='png'), \
                    patch.object(GdkPixbuf.Pixbuf, 'new_from_file_at_scale') as decode:
                with self.assertRaises(ValueError):
                    app.sddm_background_image(source.name)
            decode.assert_not_called()

    def test_only_generated_png_is_passed_to_native_install(self):
        def install(args, **kwargs):
            self.assertEqual(args[:7], ['pkexec', '/usr/bin/install', '-D', '-m', '0644', '--', args[6]])
            self.assertEqual(args[-1], '/usr/share/backgrounds/dotfiles-sddm.png')
            self.assertTrue(Path(args[6]).read_bytes().startswith(b'\x89PNG\r\n\x1a\n'))
            self.assertTrue(kwargs['check'])
            self.generated = Path(args[6])
        with patch.object(app.subprocess, 'run', side_effect=install) as run:
            app.install_sddm_background(app.sddm_background_image())
        run.assert_called_once()
        self.assertFalse(self.generated.exists(), 'temporary image must be cleaned up')

    def test_cancelled_authorization_is_reported_without_retry(self):
        with patch.object(app.subprocess, 'run', side_effect=subprocess.CalledProcessError(126, ['pkexec'])) as run:
            with self.assertRaisesRegex(RuntimeError, 'fondo anterior se conserva'):
                app.install_sddm_background(app.sddm_background_image())
        run.assert_called_once()

    @unittest.skipUnless(os.environ.get('DISPLAY'), 'GTK requires a display')
    def test_background_page_select_save_cancel_and_reset(self):
        gi.require_version('Gtk', '3.0')
        from gi.repository import Gtk, GLib
        if not Gtk.init_check()[0]:
            self.skipTest('GTK display unavailable')
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'selected.png'
            image = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 40, 20)
            image.fill(0x89b4faff)
            image.savev(str(source), 'png', [], [])
            failures = []

            def exercise(window):
                try:
                    self.assertFalse(window.get_visible())
                    window.get_child().show_all()
                    window.stack.set_visible_child_name('background')
                    self.assertFalse(window.try_button.get_sensitive())
                    window.buttons['save'].emit('clicked')
                    install.assert_not_called()
                    dialog = MagicMock()
                    dialog.run.return_value = Gtk.ResponseType.ACCEPT
                    dialog.get_filename.return_value = str(source)
                    with patch.object(Gtk, 'FileChooserNative', return_value=dialog):
                        window.sddm_choose.emit('clicked')
                    self.assertTrue(window.sddm_background_changed)
                    self.assertEqual(window.sddm_image.get_width(), 40)
                    dialog.run.return_value = Gtk.ResponseType.CANCEL
                    with patch.object(Gtk, 'FileChooserNative', return_value=dialog):
                        window.sddm_choose.emit('clicked')
                    self.assertEqual(window.sddm_image.get_width(), 40)
                    window.buttons['save'].emit('clicked')
                    deadline = time.monotonic() + 3
                    while window.working and time.monotonic() < deadline:
                        GLib.MainContext.default().iteration(False)
                        time.sleep(0.005)
                    self.assertFalse(window.working)
                    install.assert_called_once()
                    self.assertFalse(window.sddm_background_changed)
                    commit.assert_not_called()
                    window.sddm_reset.emit('clicked')
                    self.assertTrue(window.sddm_background_changed)
                    self.assertEqual(window.sddm_image.get_pixels()[-1], 0)
                    install.side_effect = RuntimeError('Autorización cancelada')
                    window.buttons['save'].emit('clicked')
                    deadline = time.monotonic() + 3
                    while window.working and time.monotonic() < deadline:
                        GLib.MainContext.default().iteration(False)
                        time.sleep(0.005)
                    self.assertTrue(window.sddm_background_changed)
                    self.assertFalse(window.try_button.get_sensitive())
                    self.assertIn('Autorización cancelada', window.status.get_text())
                    window.stack.set_visible_child_name('windows')
                    self.assertTrue(window.try_button.get_sensitive())
                except BaseException as error:
                    failures.append(error)
                finally:
                    window.get_application().quit()
                return False

            with patch.object(app, 'current', return_value=dict(app.DEFAULTS)), \
                    patch.object(app, 'commit') as commit, \
                    patch.object(app, 'install_sddm_background') as install, \
                    patch.object(app, 'SDDM_BACKGROUND', Path(directory) / 'missing.png'), \
                    patch('runpy.run_path', return_value={'build_page': lambda _: Gtk.Box()}):
                self.assertEqual(app.gui(test_hook=exercise), 0)
            if failures:
                raise failures[0]


if __name__ == '__main__':
    unittest.main()
