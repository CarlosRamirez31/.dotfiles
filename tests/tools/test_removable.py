import copy
import importlib.machinery
import importlib.util
import io
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

loader = importlib.machinery.SourceFileLoader('removable', str(Path(__file__).resolve().parents[2] / 'bin/dotfiles-removable'))
spec = importlib.util.spec_from_loader(loader.name, loader)
app = importlib.util.module_from_spec(spec)
loader.exec_module(app)
D = app.ROOT + '/drives/test'
B = app.ROOT + '/block_devices/sdb1'


def disk():
    return {D: {app.DRIVE: {'Id': 'test-id', 'TimeDetected': 1, 'TimeMediaDetected': 1,
                            'ConnectionBus': 'usb', 'Model': 'Portable disk'}},
            B: {app.BLOCK: {'Drive': D, 'HintSystem': False, 'HintIgnore': False,
                            'IdUsage': 'filesystem', 'IdType': 'ext4', 'IdUUID': 'test-uuid',
                            'IdLabel': 'Data', 'DeviceNumber': 2001, 'Size': 64 * 1024 ** 3},
                app.FILESYSTEM: {'MountPoints': []}}}


class RemovableTest(unittest.TestCase):
    def setUp(self):
        self.output = patch('sys.stdout', new_callable=io.StringIO).start()
        self.addCleanup(patch.stopall)

    def test_internal_ignored_mounted_crypto_and_loop_are_not_offered(self):
        changes = [('internal', lambda o: o[D][app.DRIVE].update(ConnectionBus='nvme')),
                   ('system', lambda o: o[B][app.BLOCK].update(HintSystem=True)),
                   ('ignored', lambda o: o[B][app.BLOCK].update(HintIgnore=True)),
                   ('mounted', lambda o: o[B][app.FILESYSTEM].update(MountPoints=[[47, 0]])),
                   ('crypto', lambda o: o[B][app.BLOCK].update(IdUsage='crypto')),
                   ('loop', lambda o: o[B][app.BLOCK].update(Drive='/'))]
        for name, change in changes:
            with self.subTest(name=name):
                objects = disk()
                change(objects)
                self.assertEqual(app.volumes(objects), [])
        self.assertEqual(len(app.volumes(disk())), 1)

    def test_unmount_requires_yes_and_preserves_busy_volume(self):
        objects = disk()
        objects[B][app.FILESYSTEM]['MountPoints'] = [[47, 0]]
        selected = app.volumes(objects, include_mounted=True)[0]
        backend = Mock()
        backend.snapshot.return_value = objects
        with patch.object(app, 'read_line', return_value='no'):
            self.assertFalse(app.confirm(backend, selected))
        backend.unmount.assert_not_called()
        with patch.object(app, 'read_line', return_value='yes'):
            self.assertTrue(app.confirm(backend, selected))
        backend.unmount.assert_called_once_with(B)
        backend.mount.assert_not_called()
        backend.unmount.side_effect = OSError('Device busy')
        with patch.object(app, 'read_line', return_value='yes'), self.assertRaises(OSError):
            app.confirm(backend, selected)

    def test_no_or_empty_answer_never_mounts(self):
        for answer in ('no', ''):
            backend = Mock()
            with patch.object(app, 'read_line', return_value=answer):
                self.assertFalse(app.confirm(backend, app.volumes(disk())[0]))
            backend.mount.assert_not_called()
            backend.snapshot.assert_not_called()

    def test_only_full_yes_mounts_the_selected_volume(self):
        backend = Mock()
        backend.snapshot.return_value = disk()
        backend.mount.return_value = '/run/media/user/Data'
        with patch.object(app, 'read_line', side_effect=['y', 'yes']):
            self.assertTrue(app.confirm(backend, app.volumes(disk())[0]))
        backend.mount.assert_called_once_with(B)

    def test_removed_replaced_or_already_mounted_volume_is_rejected(self):
        states = [{}, disk(), disk()]
        states[1][B][app.BLOCK]['DeviceNumber'] += 1
        states[2][B][app.FILESYSTEM]['MountPoints'] = [[47, 0]]
        for objects in states:
            backend = Mock()
            backend.snapshot.return_value = objects
            with patch.object(app, 'read_line', return_value='yes'):
                self.assertFalse(app.confirm(backend, app.volumes(disk())[0]))
            backend.mount.assert_not_called()

    def test_chooser_mounts_only_the_number_selected(self):
        objects = disk()
        other = B + '_second'
        objects[other] = copy.deepcopy(objects[B])
        objects[other][app.BLOCK].update(IdLabel='Other', DeviceNumber=2002)
        backend = Mock()
        backend.snapshot.return_value = objects
        backend.mount.return_value = '/run/media/user/Other'
        with patch.object(app, 'read_line', side_effect=['2', 'yes']):
            self.assertTrue(app.choose(backend))
        backend.mount.assert_called_once_with(other)

    def test_existing_drives_do_not_prompt_on_startup(self):
        arrivals = app.Arrivals(disk())
        arrivals.update(disk(), 10)
        self.assertEqual(arrivals.pending, {})

    def test_partitions_and_property_changes_produce_one_prompt(self):
        objects = disk()
        objects[B + '_second'] = copy.deepcopy(objects[B])
        arrivals = app.Arrivals({})
        arrivals.update(objects, 10)
        self.assertEqual(len(arrivals.pending), 1)
        self.assertEqual(arrivals.pending[D][1], 11)
        arrivals.pending.clear()  # Answered no / popup closed.
        arrivals.update(objects, 12)
        self.assertEqual(arrivals.pending, {})
        arrivals.update({}, 13)
        arrivals.update(objects, 14)
        self.assertEqual(len(arrivals.pending), 1)

    def test_removal_and_mount_cancel_queued_prompts(self):
        arrivals = app.Arrivals({})
        arrivals.update(disk(), 10)
        arrivals.update({}, 11)
        self.assertEqual(arrivals.pending, {})
        arrivals.update(disk(), 12)
        mounted = disk()
        mounted[B][app.FILESYSTEM]['MountPoints'] = [[47, 0]]
        arrivals.update(mounted, 13)
        self.assertEqual(arrivals.pending, {})

    def test_new_card_in_existing_reader_has_a_new_generation(self):
        empty = {D: copy.deepcopy(disk()[D])}
        empty[D][app.DRIVE]['MediaRemovable'] = True
        arrivals = app.Arrivals(empty)
        inserted = disk()
        inserted[D][app.DRIVE]['TimeMediaDetected'] = 2
        arrivals.update(inserted, 10)
        self.assertEqual(len(arrivals.pending), 1)

    def test_terminal_labels_cannot_emit_escape_sequences(self):
        self.assertNotIn('\x1b', app.clean('\x1b]0;injected\x07\nName'))
        self.assertNotIn('\n', app.clean('first\nsecond'))
        command = app.terminal_args(D, 'untrusted;$(code)')
        self.assertEqual(command[-1], 'untrusted;$(code)')
        self.assertNotIn('sh', command)
