import typescriptEslint from '@typescript-eslint/eslint-plugin'
import vue from 'eslint-plugin-vue'
import parser from 'vue-eslint-parser'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import js from '@eslint/js'
import { FlatCompat } from '@eslint/eslintrc'
import { includeIgnoreFile } from '@eslint/compat'
import globals from 'globals'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)
const gitignorePath = path.resolve(__dirname, '.gitignore')
const compat = new FlatCompat({
  baseDirectory: __dirname,
  recommendedConfig: js.configs.recommended,
  allConfig: js.configs.all,
})

export default [
  ...compat.extends('eslint:recommended', 'plugin:@typescript-eslint/eslint-recommended', 'plugin:@typescript-eslint/recommended', 'prettier'),
  ...vue.configs['flat/recommended'],
  {
    plugins: {
      '@typescript-eslint': typescriptEslint,
    },
    languageOptions: {
      parser: parser,
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: globals.browser,
      parserOptions: {
        parser: '@typescript-eslint/parser',
      },
    },
    rules: {
      'no-unused-vars': 'off',
      '@typescript-eslint/no-unused-vars': 'error',
      'no-irregular-whitespace': ['error', { skipStrings: true, skipTemplates: true }],
    },
    files: ['**/*.vue', '**/*.js', '**/*.ts'],
  },
  includeIgnoreFile(gitignorePath),
  {},
]
