import { fileURLToPath, URL } from 'url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { nodePolyfills } from 'vite-plugin-node-polyfills';

// https://vitejs.dev/config/
export default defineConfig(({ command, mode }) => {
	return {
		plugins: [vue({
			template: {
				compilerOptions: {
					isCustomElement: (tag) => ['swiper-slide', 'swiper-container', 'swiper-pagination'].includes(tag)
				}
			}
		}),
		nodePolyfills({
			globals: {
				Buffer: true,
				global: true,
				process: true,
			}
		})],
		resolve: {
			alias: {
				'@': fileURLToPath(new URL('./src', import.meta.url)),
				url: "rollup-plugin-node-polyfills/polyfills/url",
				util: "rollup-plugin-node-polyfills/polyfills/util",
				querystring: "rollup-plugin-node-polyfills/polyfills/qs",
				mqtt: "mqtt/dist/mqtt.esm",
			}
		},
		optimizeDeps: {
			rolldownOptions: {
				transform: {
					define: {
						global: "globalThis",
					},
				},
			},
		},
		server: command === 'serve' && mode !== 'test' ? {
			proxy: {
				"/ws": {
					target: "ws://localhost:9003",
					ws: true,
				},
			},
		} : undefined,
	};
});
