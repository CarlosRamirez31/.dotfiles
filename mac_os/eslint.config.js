import js from '@eslint/js';
import tseslint from 'typescript-eslint';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import prettier from 'eslint-config-prettier';

export default tseslint.config(
  { ignores: ['dist/**', '.runtime/**', 'src-tauri/**', 'node_modules/**'] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ['src/**/*.{ts,tsx}'],
    plugins: { 'react-hooks': reactHooks, 'react-refresh': reactRefresh },
    rules: {
      ...reactHooks.configs.recommended.rules,
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
    },
  },
  {
    files: ['src/**/*.tsx'],
    ignores: ['src/main.tsx'],
    rules: {
      'no-restricted-syntax': [
        'error',
        {
          selector: 'CallExpression[callee.type="Identifier"]:not([callee.name=/^use[A-Z]/])',
          message: 'Call hooks here; calculate values in hooks or presentation functions.',
        },
        {
          selector: 'CallExpression[callee.type="MemberExpression"]:not([callee.property.name="map"])',
          message: 'Only declarative list mapping belongs in views; move other calls to hooks.',
        },
        { selector: 'IfStatement', message: 'Move decisions into a hook or presentation function.' },
        { selector: 'TryStatement', message: 'Handle effects and errors in a hook.' },
        { selector: 'ThrowStatement', message: 'Views only render prepared state.' },
        { selector: 'ConditionalExpression', message: 'Prepare labels and choices outside JSX.' },
        { selector: 'AssignmentExpression', message: 'Keep mutations in hooks or functions.' },
        {
          selector: 'CallExpression[callee.name=/^(useState|useEffect|useReducer|fetch|invoke)$/]',
          message: 'Extract state, effects and IO to hooks.',
        },
        {
          selector: 'JSXAttribute ArrowFunctionExpression',
          message: 'Bind a prepared hook handler instead of inline logic.',
        },
        {
          selector: 'ImportDeclaration[source.value=/infrastructure/]',
          message: 'Views depend on hooks and ports, not concrete adapters.',
        },
      ],
    },
  },
  {
    files: ['src/modules/**/application/**/*.ts', 'src/modules/**/domain/**/*.ts'],
    rules: {
      'no-restricted-imports': [
        'error',
        {
          patterns: [
            {
              group: ['**/infrastructure/**', '**/presentation/**', '@tauri-apps/**'],
              message: 'Application and domain depend on ports and internal types.',
            },
          ],
        },
      ],
    },
  },
  prettier,
);
