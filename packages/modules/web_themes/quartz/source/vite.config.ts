import { fileURLToPath, URL } from 'url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

// https://vitejs.dev/config/
export default defineConfig(({ command, mode }) => ({
  plugins: [vue(), tailwindcss()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server:
    command === 'serve' && mode !== 'test'
      ? {
          proxy: {
            '/ws': {
              target: 'ws://localhost:9003',
              ws: true,
            },
          },
        }
      : undefined,
}))
