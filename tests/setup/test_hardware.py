"""Exercise GPU selection without installing packages or rebuilding boot images."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[2]


class Hardware(unittest.TestCase):
    def run_hardware(self, vendor, device, stock_kernel=True):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            modules = root / 'modules'
            modules.mkdir()
            pci = root / 'pci/0000:01:00.0'
            pci.mkdir(parents=True)
            (pci / 'vendor').write_text(vendor)
            (pci / 'device').write_text(device)
            script = (REPO / 'setup/modules/hardware.sh').read_text()
            (modules / 'hardware.sh').write_text(
                script.replace('/sys/bus/pci/devices/', str(root / 'pci') + '/'))
            (root / 'lib.sh').write_text('''
require_arch_user() { :; }
install_packages() { printf 'packages %s\\n' "$*" >> "$CALL_LOG"; }
link_component() { :; }
systemd-detect-virt() { echo kvm; }
systemctl() { :; }
sudo() { printf 'sudo %s\\n' "$*" >> "$CALL_LOG"; }
pacman() { [[ "$*" == '-Q linux' && "$STOCK_KERNEL" == 1 ]]; }
''')
            log = root / 'calls'
            result = subprocess.run(['bash', str(modules / 'hardware.sh')],
                                    env=dict(os.environ, CALL_LOG=str(log),
                                             STOCK_KERNEL=str(int(stock_kernel))),
                                    text=True, capture_output=True, check=True)
            return log.read_text(), result.stdout

    def test_rtx4050_installs_driver_before_rebuilding_boot_images(self):
        log, output = self.run_hardware('0x10de', '0x28e1')
        self.assertIn('packages nvidia-open nvidia-utils\nsudo mkinitcpio -P\n', log)
        self.assertIn('reboot', output)

    def test_other_gpus_do_not_install_nvidia_or_rebuild_boot(self):
        for vendor, device in [('0x1002', '0x1900'), ('0x10de', '0x1b80')]:
            with self.subTest(vendor=vendor, device=device):
                log, _ = self.run_hardware(vendor, device)
                self.assertNotIn('nvidia', log)
                self.assertNotIn('mkinitcpio', log)

    def test_other_kernel_is_left_unchanged_with_explanation(self):
        log, output = self.run_hardware('0x10de', '0x28e1', stock_kernel=False)
        self.assertNotIn('nvidia', log)
        self.assertNotIn('mkinitcpio', log)
        self.assertIn('without the stock linux kernel', output)


if __name__ == '__main__':
    unittest.main()
