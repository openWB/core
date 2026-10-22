import { fileURLToPath, URL } from 'url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig(({ command, mode }) => ({
  plugins: [vue()],
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
