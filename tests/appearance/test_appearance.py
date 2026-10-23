"""Preview transactions never modify the live host in these tests."""
import importlib.machinery
import importlib.util
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

loader = importlib.machinery.SourceFileLoader("appearance", str(Path(__file__).resolve().parents[2] / "bin/dotfiles-appearance"))
spec = importlib.util.spec_from_loader(loader.name, loader)
app = importlib.util.module_from_spec(spec)
loader.exec_module(app)
real_compositor = app.compositor


class AppearanceTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name, value in (("RUNTIME", self.root / "runtime"), ("SAVED", self.root / "config/appearance.json")):
            patcher = patch.object(app, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.wm = patch.object(app, "wm").start()
        self.compositor = patch.object(app, "compositor").start()
        self.process = patch.object(app.subprocess, "Popen").start()
        self.addCleanup(patch.stopall)

    def test_rejects_invalid_values_and_code_in_colors(self):
        for value in (dict(gap=999), dict(border=True), dict(shadows="false"), dict(accent='";os.execute("bad")'), dict(backend="xrender")):
            with self.assertRaises(ValueError):
                app.validate(value)

    def test_config_preserves_backend_and_exclusions(self):
        base = 'backend = "glx";\nvsync = true;\ncorner-radius = 10;\nshadow-exclude = [ "class_g = \'Keep\'" ];\n'
        result = app.picom_config(base, dict(app.DEFAULTS, corners=20, shadow_opacity=30))
        self.assertIn('backend = "glx";', result)
        self.assertIn('shadow-exclude = [ "class_g = \'Keep\'" ];', result)
        self.assertEqual(result.count("corner-radius ="), 1)
        self.assertIn("corner-radius = 20;", result)
        self.assertIn("shadow-opacity = 0.3;", result)

    def test_preview_reverts_without_creating_saved_preferences(self):
        changed = dict(app.DEFAULTS, corners=20, gap=12)
        token = app.preview(changed)
        self.assertEqual(app.current(), changed)
        self.assertFalse(app.SAVED.exists())
        self.assertTrue(app.revert(token))
        self.assertEqual(app.current(), app.DEFAULTS)
        self.assertFalse(app.SAVED.exists())

    def test_save_confirms_trial_and_stale_watchdog_cannot_undo_it(self):
        changed = dict(app.DEFAULTS, border=2, accent="#abcdef")
        token = app.preview(changed)
        app.commit(changed)
        self.assertEqual(app.saved(), changed)
        self.assertFalse(app.revert(token))
        self.assertEqual(app.current(), changed)

    def test_expired_watchdog_restores_previous_state(self):
        token = app.preview(dict(app.DEFAULTS, shadows=False))
        marker = app.read(app.RUNTIME / "preview.json")
        marker["deadline"] = 0
        app.write(app.RUNTIME / "preview.json", marker)
        app.watch(token)
        self.assertEqual(app.current(), app.DEFAULTS)
        self.assertFalse((app.RUNTIME / "preview.json").exists())

    def test_only_window_changes_do_not_restart_compositor(self):
        app.commit(dict(app.DEFAULTS, gap=15, border=3))
        self.compositor.assert_not_called()
        self.wm.assert_called_once()

    def test_window_only_trial_also_reverts_without_restarting_compositor(self):
        token = app.preview(dict(app.DEFAULTS, gap=12))
        app.revert(token)
        self.compositor.assert_not_called()

    def test_revert_uses_actual_previous_configuration(self):
        previous = dict(app.DEFAULTS, gap=11, inactive_opacity=90)
        app.commit(previous)
        token = app.preview(dict(previous, gap=2))
        app.revert(token)
        self.assertEqual(app.current(), previous)
        self.assertEqual(app.saved(), previous)

    def test_failed_preview_rolls_back_and_clears_trial(self):
        self.wm.side_effect = [RuntimeError("WM failed"), None]
        with self.assertRaises(RuntimeError):
            app.preview(dict(app.DEFAULTS, corners=20))
        self.assertEqual(app.current(), app.DEFAULTS)
        self.assertFalse((app.RUNTIME / "preview.json").exists())
        self.assertFalse(app.SAVED.exists())

    def test_rejects_overlapping_trials(self):
        token = app.preview(dict(app.DEFAULTS, gap=8))
        with self.assertRaises(ValueError):
            app.preview(dict(app.DEFAULTS, gap=12))
        self.assertEqual(app.read(app.RUNTIME / "preview.json")["token"], token)

    def test_login_restores_saved_preferences_instead_of_old_runtime_preview(self):
        stored = dict(app.DEFAULTS, corners=22, shadow_opacity=45, inactive_opacity=92)
        app.write(app.SAVED, stored)
        app.write(app.RUNTIME / "live.json", dict(app.DEFAULTS, corners=0, shadows=False))
        app.write(app.RUNTIME / "preview.json", dict(token="old-session"))
        app.restore_compositor()
        self.compositor.assert_called_once_with(stored)
        self.assertEqual(app.current(), stored)
        self.assertEqual(app.saved(), stored)
        self.assertFalse((app.RUNTIME / "preview.json").exists())

    def test_monitor_does_not_restart_a_healthy_compositor(self):
        with patch.object(app, "active_compositors", return_value=[123]):
            self.assertFalse(app.ensure_compositor())
        self.compositor.assert_not_called()

    def test_monitor_recovers_missing_compositor_using_saved_settings(self):
        stored = dict(app.DEFAULTS, corners=18, shadows=False)
        app.write(app.SAVED, stored)
        app.write(app.RUNTIME / "live.json", dict(app.DEFAULTS, corners=0))
        with patch.object(app, "active_compositors", return_value=[]):
            self.assertTrue(app.ensure_compositor())
        self.compositor.assert_called_once_with(stored)
        self.assertEqual(app.current(), stored)

    def test_monitor_preserves_an_active_temporary_preview(self):
        temporary = dict(app.DEFAULTS, inactive_opacity=85)
        app.write(app.RUNTIME / "live.json", temporary)
        app.write(app.RUNTIME / "preview.json", dict(token="trial", deadline=time.time() + 20))
        with patch.object(app, "active_compositors", return_value=[]):
            app.ensure_compositor()
        self.compositor.assert_called_once_with(temporary)
        self.assertFalse(app.SAVED.exists())

    def test_monitor_does_not_queue_behind_a_save_or_preview(self):
        with app.locked(), patch.object(app, "active_compositors") as active:
            self.assertFalse(app.ensure_compositor())
            active.assert_not_called()
        self.compositor.assert_not_called()

    def test_compositor_keeps_glx_and_reports_failure_without_switching_backend(self):
        base = self.root / "base.conf"
        base.write_text('backend = "glx";\nvsync = true;\n')
        with patch.object(app, "BASE", base), patch.object(app, "launch_compositor", side_effect=RuntimeError("GLX failed")) as launch:
            with self.assertRaisesRegex(RuntimeError, "GLX failed"):
                real_compositor(app.DEFAULTS)
        self.assertEqual(launch.call_count, 1)
        self.assertIn('backend = "glx";', launch.call_args.args[0])

    def test_every_numeric_setting_accepts_both_displayed_limits(self):
        for key, limits in app.RANGES.items():
            for value in limits:
                with self.subTest(setting=key, value=value):
                    settings = dict(app.DEFAULTS, **{key: value})
                    app.commit(settings)
                    self.assertEqual(app.saved()[key], value)
                    self.assertEqual(app.current()[key], value)
                    self.assertIn(app.PICOM.get(key, key), app.picom_config("", settings) if key in app.PICOM else key)

    @unittest.skipUnless(os.environ.get("DISPLAY"), "GTK signal tests require an X11 display")
    def test_actual_gtk_controls_and_action_signals_without_showing_a_window(self):
        import gi
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk, Gdk, GLib
        if not Gtk.init_check()[0]:
            self.skipTest("GTK display is unavailable")
        failures = []
        def exercise(window):
            application = window.get_application()
            def wait():
                deadline = time.monotonic() + 5
                while window.working and time.monotonic() < deadline:
                    while GLib.MainContext.default().pending():
                        GLib.MainContext.default().iteration(False)
                    time.sleep(0.005)
                self.assertFalse(window.working, "GTK worker did not finish")
                self.assertNotIn("No se pudo aplicar", window.status.get_text())
            try:
                self.assertFalse(window.get_visible(), "test window must stay hidden")
                for key, limits in app.RANGES.items():
                    for value in limits:
                        window.widgets[key].set_value(value)
                        self.assertEqual(window.values[key], value)
                    window.widgets[key].set_value(limits[1] + 999)
                    self.assertEqual(window.values[key], limits[1], "GTK must clamp oversized input")
                for key in ("shadows", "fading"):
                    for value in (False, True):
                        window.widgets[key].set_active(value)
                        self.assertEqual(window.values[key], value)
                color = Gdk.RGBA(); color.parse("#123456")
                window.widgets["accent"].set_rgba(color)
                window.widgets["accent"].emit("color-set")
                self.assertEqual(window.values["accent"], "#123456")
                for index, preset in enumerate(app.PRESETS.values(), 1):
                    window.presets.set_active(index)
                    self.assertEqual(window.values, preset)
                window.buttons["reset"].emit("clicked")
                self.assertEqual(window.values, app.DEFAULTS)
                window.widgets["gap"].set_value(100)
                window.buttons["preview"].emit("clicked"); wait()
                self.assertIsNotNone(window.token)
                self.assertEqual(app.current()["gap"], 100)
                window.buttons["cancel"].emit("clicked"); wait()
                self.assertIsNone(window.token)
                self.assertEqual(app.current(), app.DEFAULTS)
                window.widgets["corners"].set_value(99)
                window.buttons["save"].emit("clicked"); wait()
                self.assertEqual(app.saved()["corners"], 99)
                window.widgets["corners"].set_value(0)
                window.buttons["preview"].emit("clicked"); wait()
                token = window.token
                app.revert(token)
                window.tick()
                self.assertIsNone(window.token)
                self.assertEqual(window.values["corners"], 99)
                self.process.reset_mock()
                window.wallpaper_button.emit("clicked")
                self.assertEqual(self.process.call_args.args[0], [str(Path.home() / ".local/bin/dotfiles-wallpaper-picker")])
                window.widgets["corners"].set_value(2)
                window.buttons["preview"].emit("clicked"); wait()
                self.assertTrue(window.close())
                wait()
                self.assertFalse((app.RUNTIME / "preview.json").exists())
                self.assertEqual(app.current()["corners"], 99)
            except BaseException as error:
                failures.append(error)
            finally:
                application.quit()
            return False
        self.assertEqual(app.gui(test_hook=exercise), 0)
        if failures:
            raise failures[0]


if __name__ == "__main__":
    unittest.main()
