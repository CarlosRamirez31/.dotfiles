import importlib.machinery
import importlib.util
from pathlib import Path
import unittest
loader = importlib.machinery.SourceFileLoader('polybar_style', str(Path(__file__).resolve().parents[2] / 'bin/dotfiles-polybar-style'))
spec = importlib.util.spec_from_loader(loader.name, loader)
style = importlib.util.module_from_spec(spec)
loader.exec_module(style)


class StyleTest(unittest.TestCase):
    def test_application_scale_does_not_change_independent_bar_size(self):
        self.assertEqual(style.style({'scale': 125, 'polybar_scale': 100})['POLYBAR_HEIGHT'], '30')
        self.assertEqual(style.style({'scale': 125, 'polybar_scale': 125})['POLYBAR_HEIGHT'], '38')
        self.assertEqual(style.style({'scale': 100, 'polybar_scale': 150})['POLYBAR_HEIGHT'], '45')

    def test_text_and_icons_follow_the_bar_size(self):
        values = style.style({'scale': 100, 'polybar_scale': 150})
        self.assertIn('size=18.75;', values['POLYBAR_FONT_0'])
        self.assertIn('size=28.5;', values['POLYBAR_FONT_1'])


    def test_corrupt_saved_appearance_does_not_crash_the_panel(self):
        for value in ({'polybar_scale': 'bad'}, {'polybar_scale': None},
                      {'polybar_scale': 'nan'}, {'polybar_scale': 'inf'}, [], None):
            self.assertEqual(style.style(value)['POLYBAR_HEIGHT'], '30')
