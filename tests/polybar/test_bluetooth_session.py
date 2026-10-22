"""Exercise the BlueZ agent without touching the machine's Bluetooth adapter."""

from pathlib import Path
import json
import runpy
import tempfile
import time
import unittest
from unittest.mock import patch

from gi.repository import GLib

PROGRAM = Path(__file__).resolve().parents[2] / "bin/dotfiles-bluetooth-session"
MODULE = runpy.run_path(str(PROGRAM))
Session = MODULE["Session"]
ADAPTER = "/org/bluez/hci0"
DEVICE = ADAPTER + "/dev_AA_BB_CC_DD_EE_FF"


class Result:
    def __init__(self, value):
        self.value = value

    def unpack(self):
        return (self.value,)


class Invocation:
    def __init__(self):
        self.replies = []

    def return_value(self, value):
        self.replies.append(("value", value))

    def return_dbus_error(self, name, message):
        self.replies.append((name, message))


class FakeBus:
    def __init__(self):
        self.async_calls = []

    def register_object(self, *_args):
        return 1

    def signal_subscribe(self, *_args):
        return 1

    def call_sync(self, *_args):
        return Result(":1.42")

    def call(self, *args):
        self.async_calls.append(args)

    def call_finish(self, _result):
        return None


class FakeBluetooth:
    def __init__(self):
        self.bus = FakeBus()
        self.adapter = ADAPTER
        self.properties = {"Powered": True}
        self.objects = {
            ADAPTER: {"org.bluez.Adapter1": self.properties},
            DEVICE: {"org.bluez.Device1": {
                "Adapter": ADAPTER, "Address": "AA:BB:CC:DD:EE:FF", "Alias": "Auriculares <Casa>",
            }},
        }
        self.calls = []

    def call(self, *args):
        self.calls.append(args)
        return Result(self.objects)


class PairingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        with patch.dict(Session.__init__.__globals__, {"Bluetooth": FakeBluetooth}):
            self.session = Session(Path(self.temporary.name))
        self.session.pairing = DEVICE

    def request(self, method, signature, values, sender=":1.42"):
        invocation = Invocation()
        self.session.agent_call(None, sender, None, None, method,
                                GLib.Variant(signature, values), invocation)
        return invocation

    def test_numeric_comparison_waits_for_the_user(self):
        invocation = self.request("RequestConfirmation", "(ou)", (DEVICE, 42))
        self.assertEqual(invocation.replies, [])
        self.assertEqual(self.session.request["code"], "000042")
        self.session.answer("stale-request:yes")
        self.assertEqual(invocation.replies, [])
        self.session.answer(self.session.request["id"] + ":yes")
        self.assertEqual(invocation.replies, [("value", None)])

    def test_agent_rejects_other_callers_and_devices(self):
        for device, sender in [(DEVICE, ":1.99"), (ADAPTER + "/other", ":1.42")]:
            invocation = self.request("RequestConfirmation", "(ou)", (device, 123456), sender)
            self.assertEqual(invocation.replies[0][0], "org.bluez.Error.Rejected")
            self.assertIsNone(self.session.request)

    def test_passkey_validation_preserves_the_pending_request(self):
        invocation = self.request("RequestPasskey", "(o)", (DEVICE,))
        token = self.session.request["id"]
        with self.assertRaises(ValueError):
            self.session.answer(token + ":1000000")
        self.assertEqual(invocation.replies, [])
        self.session.answer(token + ":000123")
        self.assertEqual(invocation.replies[0][1].unpack(), (123,))

    def test_pin_and_cancellation(self):
        invocation = self.request("RequestPinCode", "(o)", (DEVICE,))
        self.session.answer(self.session.request["id"] + ":A123")
        self.assertEqual(invocation.replies[0][1].unpack(), ("A123",))
        invocation = self.request("RequestAuthorization", "(o)", (DEVICE,))
        self.session.reject_request()
        self.assertEqual(invocation.replies[0][0], "org.bluez.Error.Canceled")

    def test_display_passkey_does_not_auto_confirm(self):
        invocation = self.request("DisplayPasskey", "(ouq)", (DEVICE, 7, 0))
        self.assertEqual(invocation.replies, [("value", None)])
        self.assertEqual(self.session.request["code"], "000007")
        self.assertIsNone(self.session.pending)

    def test_pair_registers_an_agent_and_connects_only_after_success(self):
        self.session.pair("AA:BB:CC:DD:EE:FF")
        self.assertEqual(self.session.bt.calls[0][2], "RegisterAgent")
        call = self.session.bt.bus.async_calls[0]
        self.assertEqual(call[1:4], (DEVICE, "org.bluez.Device1", "Pair"))
        self.assertFalse(any(item[2] == "Set" for item in self.session.bt.calls))
        call[-1](self.session.bt.bus, None)
        self.assertEqual(self.session.bt.calls[-1][2], "Set")
        self.assertEqual(self.session.bt.bus.async_calls[-1][3], "Connect")

    def test_only_our_discovery_session_is_stopped(self):
        self.session.stop_scan()
        self.assertEqual(self.session.bt.calls, [])
        self.session.scanning = True
        self.session.stop_scan()
        self.assertEqual(self.session.bt.calls, [(ADAPTER, "org.bluez.Adapter1", "StopDiscovery")])

    def test_cancelled_pairing_does_not_trust_or_connect(self):
        self.session.pair("AA:BB:CC:DD:EE:FF")
        self.session.cancel_pairing()
        self.session.bt.bus.async_calls[0][-1](self.session.bt.bus, None)
        self.assertEqual(len(self.session.bt.bus.async_calls), 1)
        self.assertFalse(any(item[2] == "Set" for item in self.session.bt.calls))
        self.assertEqual(self.session.message, "Operación cancelada.")

    def test_cancel_connect_uses_disconnect(self):
        self.session.pairing = None
        self.session.operation_path = DEVICE
        self.session.operation_method = "Connect"
        self.session.cancel_pairing()
        self.assertEqual(self.session.bt.calls[-1], (DEVICE, "org.bluez.Device1", "Disconnect"))

    def snapshot_name(self):
        self.session.seen[DEVICE] = time.monotonic()
        self.session.publish()
        snapshot = json.loads((self.session.folder / "state.json").read_text())["snapshot"]
        return next(line.split("\t")[4] for line in snapshot.splitlines() if line.startswith("device\t"))

    def test_mac_alias_uses_the_advertised_name(self):
        device = self.session.bt.objects[DEVICE]["org.bluez.Device1"]
        for alias in ("AA:BB:CC:DD:EE:FF", "aa-bb-cc-dd-ee-ff", "AABBCCDDEEFF"):
            with self.subTest(alias=alias):
                device.update(Alias=alias, Name="JBL Tune 520BT")
                self.assertEqual(self.snapshot_name(), "JBL Tune 520BT")

    def test_unresolved_device_never_uses_the_mac_as_its_label(self):
        self.session.bt.objects[DEVICE]["org.bluez.Device1"]["Alias"] = "AA-BB-CC-DD-EE-FF"
        self.assertEqual(self.snapshot_name(), "Dispositivo sin identificar")

    def test_name_appears_after_discovery_and_is_preserved(self):
        device = self.session.bt.objects[DEVICE]["org.bluez.Device1"]
        device["Alias"] = "AA-BB-CC-DD-EE-FF"
        self.assertEqual(self.snapshot_name(), "Dispositivo sin identificar")
        device["Name"] = "Sony WH-1000XM5"
        self.assertEqual(self.snapshot_name(), "Sony WH-1000XM5")
        del device["Name"]
        self.assertEqual(self.snapshot_name(), "Sony WH-1000XM5")

    def test_friendly_alias_is_preserved(self):
        device = self.session.bt.objects[DEVICE]["org.bluez.Device1"]
        device.update(Alias="Mis audífonos", Name="Factory name")
        self.assertEqual(self.snapshot_name(), "Mis audífonos")


if __name__ == "__main__":
    unittest.main()
