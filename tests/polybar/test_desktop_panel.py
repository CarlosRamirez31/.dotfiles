"""Player selection and capability checks without changing a real player."""
import contextlib
import importlib.machinery
import importlib.util
import io
from pathlib import Path
import unittest
from unittest.mock import Mock, patch
import tempfile
import json

loader = importlib.machinery.SourceFileLoader(
    "desktop_panel", str(Path(__file__).resolve().parents[2] / "bin/dotfiles-desktop-panel"))
spec = importlib.util.spec_from_loader(loader.name, loader)
panel = importlib.util.module_from_spec(spec)
loader.exec_module(panel)


class DesktopPanelTest(unittest.TestCase):
    def test_prefers_playing_player_and_preserves_unicode(self):
        bus = Mock()
        bus.call_sync.return_value.unpack.return_value = (["org.mpris.MediaPlayer2.a", "org.mpris.MediaPlayer2.b"],)
        states = [{"PlaybackStatus": "Paused"}, {"PlaybackStatus": "Playing",
                  "Metadata": {"xesam:title": "Éxtasis <live>\ntrack", "xesam:artist": ["Uno", "Dos"]}}]
        with patch.object(panel.Gio, "bus_get_sync", return_value=bus), patch.object(panel, "properties", side_effect=states):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                panel.music()
        self.assertIn("player\torg.mpris.MediaPlayer2.b\n", output.getvalue())
        self.assertIn("title\tÉxtasis <live> track\n", output.getvalue())
        self.assertIn("artist\tUno, Dos\n", output.getvalue())

    def test_no_players_is_normal_empty_state(self):
        bus = Mock()
        bus.call_sync.return_value.unpack.return_value = ([],)
        with patch.object(panel.Gio, "bus_get_sync", return_value=bus):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                panel.music()
        self.assertEqual(output.getvalue(), "state\tempty\n")

    def test_unavailable_control_does_not_send_action(self):
        with patch.object(panel.Gio, "bus_get_sync"), patch.object(panel, "properties", return_value={"CanControl": True, "CanGoNext": False}), patch.object(panel, "call") as call:
            panel.action("org.mpris.MediaPlayer2.test", "Next", 0)
            call.assert_not_called()

    def test_seek_uses_current_track_and_clamps_to_duration(self):
        props = {"CanControl": True, "CanSeek": True,
                 "Metadata": {"mpris:trackid": "/track/one", "mpris:length": 9000000}}
        with patch.object(panel.Gio, "bus_get_sync"), patch.object(panel, "properties", return_value=props), patch.object(panel, "call") as call:
            panel.action("org.mpris.MediaPlayer2.test", "SetPosition", 99)
            self.assertEqual(call.call_args.args[-1].unpack(), ("/track/one", 9000000))

    def test_rejects_unrelated_bus_names(self):
        with self.assertRaises(ValueError):
            panel.action("org.freedesktop.Notifications", "Next", 0)

    def test_remote_file_hosts_are_not_local_artwork(self):
        self.assertEqual(panel.cover("file://remote/etc/passwd"), "")

    def test_connected_wifi_takes_priority_over_unavailable_ethernet(self):
        wifi = dict(name="wlo1", kind="wifi", connected=True)
        ethernet = dict(name="enp2s0", kind="ethernet", connected=False)
        self.assertIs(panel.network_device([ethernet, wifi]), wifi)

    def test_wifi_toggle_only_changes_wifi_radio(self):
        device = dict(name="wlo1", kind="wifi", connected=True)
        with patch.object(panel, "connections", return_value=[device]), patch.object(panel, "run", side_effect=["enabled", ""]) as run:
            panel.toggle_switch("network")
            self.assertEqual(run.call_args.args, ("nmcli", "radio", "wifi", "off"))

    def test_airplane_restores_only_previously_enabled_radio(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "airplane.json"
            path.write_text(json.dumps({"1": "unblocked", "2": "blocked"}))
            devices = [{"id": 1, "soft": "blocked"}, {"id": 2, "soft": "blocked"}]
            with patch.object(panel, "state_file", return_value=path), patch.object(panel, "radios", return_value=devices), patch.object(panel, "run") as run:
                panel.toggle_switch("airplane")
                run.assert_called_once_with("rfkill", "unblock", "1")
                self.assertFalse(path.exists())

    def test_nightlight_restores_prior_gamma(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nightlight.json"
            with patch.object(panel, "state_file", return_value=path), patch.object(panel, "gamma_outputs", return_value={"DP-1": "1:0.9:0.8"}), patch.object(panel, "run") as run:
                panel.toggle_switch("nightlight")
                run.assert_called_with("xrandr", "--output", "DP-1", "--gamma", "1:0.82:0.64")
                panel.toggle_switch("nightlight")
                run.assert_called_with("xrandr", "--output", "DP-1", "--gamma", "1:0.9:0.8")
                self.assertFalse(path.exists())

    def test_shuffle_sets_mpris_property(self):
        with patch.object(panel.Gio, "bus_get_sync"), patch.object(panel, "properties", return_value={"CanControl": True, "Shuffle": False}), patch.object(panel, "call") as call:
            panel.action("org.mpris.MediaPlayer2.test", "Shuffle", 0)
            self.assertEqual(call.call_args.args[-1].unpack(), (panel.PLAYER, "Shuffle", True))


if __name__ == "__main__":
    unittest.main()
