import js from "@eslint/js"
import pluginVue from "eslint-plugin-vue"

export default [
  js.configs.recommended,
  ...pluginVue.configs['flat/recommended'],
  {
    files: ["**/*.{vue,js,jsx,cjs,mjs}"],
    languageOptions: {
      ecmaVersion: "latest",
    },
  }
]
