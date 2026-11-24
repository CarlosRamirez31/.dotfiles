import json
from pathlib import Path
import shutil
import subprocess
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which('node'), 'Node is required for local avatars')
class AvatarCatalogue(unittest.TestCase):
    def request(self, value):
        return subprocess.run(['node', str(ROOT / 'libexec/avatar/render.mjs')],
                              input=json.dumps(value), capture_output=True, text=True, timeout=30)

    def test_entire_catalogue_renders_offline_with_license_metadata(self):
        result = self.request({'action': 'catalog'})
        self.assertEqual(result.returncode, 0, result.stderr)
        items = json.loads(result.stdout)
        self.assertEqual(len(items), 61)
        self.assertIn('pixel-art', {item['name'] for item in items})
        for item in items:
            with self.subTest(style=item['name']):
                self.assertTrue(item['meta']['license']['text'])
                self.assertTrue(ET.fromstring(item['svg']).tag.endswith('svg'))

    def test_customization_and_invalid_style(self):
        result = self.request({'style': 'pixel-art', 'options': {'seed': 'avatar-test'}})
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertIn('hairVariant', data['fields'])
        self.assertTrue(data['svg'])
        result = self.request({'style': '../../not-a-style', 'options': {}})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Unknown style', result.stderr)

    def test_visual_variants_are_complete_when_returned_through_a_pipe(self):
        result = self.request({'action': 'variants', 'style': 'pixel-art',
                               'field': 'hairVariant', 'options': {'seed': 'test'}})
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(len(data), 45)
        self.assertEqual(len({item['svg'] for item in data}), 45)
