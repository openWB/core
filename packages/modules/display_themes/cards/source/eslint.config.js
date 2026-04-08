import { defineConfig } from "eslint/config"
import js from "@eslint/js"
import globals from "globals"
import pluginVue from "eslint-plugin-vue"

export default defineConfig([
  js.configs.recommended,
  ...pluginVue.configs['flat/recommended'],
  {
    files: ["**/*.{vue,js,jsx,cjs,mjs}"],
    languageOptions: {
      ecmaVersion: "latest",
      globals: {
        ...globals.browser,
      },
    },
  }
]);
