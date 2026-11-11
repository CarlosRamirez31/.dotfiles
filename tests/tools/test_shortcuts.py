import importlib.machinery
import importlib.util
from pathlib import Path
import unittest

loader = importlib.machinery.SourceFileLoader('shortcuts', str(Path(__file__).resolve().parents[2] / 'bin/dotfiles-shortcuts'))
spec = importlib.util.spec_from_loader(loader.name, loader)
shortcuts = importlib.util.module_from_spec(spec)
loader.exec_module(shortcuts)


class ShortcutsTest(unittest.TestCase):
    def test_file_clipboard_and_tray_controls_are_searchable(self):
        entries = list(shortcuts.entries())
        self.assertTrue(any(category == 'Yazi' and key == 'Ctrl+V' and 'portapapeles' in description
                            for _, category, key, description in entries))
        self.assertTrue(any(category == 'File tray' and 'Ctrl+X' in key and 'corte' in description
                            for _, category, key, description in entries))
        self.assertTrue(any(key == 'Alt+F5' for _, _, key, _ in entries))
        self.assertTrue(any(key == 'Alt+M' for _, _, key, _ in entries))
        self.assertTrue(any(key == 'dotfiles-removable menu' for _, _, key, _ in entries))
