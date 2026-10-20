import process from 'node:process';
import { URL } from 'node:url';
import { spawnSync } from 'node:child_process';
import { readdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
const root = fileURLToPath(new URL('../', import.meta.url));
function find(directory) {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) =>
    entry.isDirectory()
      ? find(resolve(directory, entry.name))
      : entry.name.endsWith('.test.mjs')
        ? [resolve(directory, entry.name)]
        : [],
  );
}
function run(command, args) {
  const result = spawnSync(command, args, { cwd: root, stdio: 'inherit' });
  if (result.error || result.status !== 0) process.exit(result.status || 1);
}
const suite = process.argv[2] ?? 'all';
if (!['all', 'frontend', 'rust', 'python', 'models'].includes(suite)) throw new Error('unknown_suite');
if (suite === 'all' || suite === 'frontend') {
  const files = find(resolve(root, 'src'));
  if (!files.length) throw new Error('no_frontend_tests');
  run(process.execPath, ['--experimental-strip-types', '--test', ...files]);
}
if (suite === 'all' || suite === 'rust' || suite === 'models')
  run('cargo', [
    'test',
    '--locked',
    '--manifest-path',
    'src-tauri/Cargo.toml',
    ...(suite === 'models' ? ['real_personal_voice_adapter_roundtrip', '--', '--ignored'] : []),
  ]);
if (suite === 'all' || suite === 'python')
  run(process.env.MIC_TEST_PYTHON ?? resolve(root, '.runtime/personal-voice/venv/bin/python'), [
    '-I',
    'test/python.py',
  ]);
