import { fileURLToPath, URL } from 'url'
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
// Node polyfills caused a dependency-scan failure during Vite pre-bundling
// (see: "Failed to run dependency scan. Not implemented").
// Temporarily disable the plugin; re-enable only if needed.

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
		// nodePolyfills() removed to avoid dependency-scan error during pre-bundling
		// Re-enable here if you need Node global shims in the browser build
	],
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
