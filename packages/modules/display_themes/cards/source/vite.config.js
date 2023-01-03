import { fileURLToPath, URL } from "node:url";

import { defineConfig } from "vite";
import Vue from "@vitejs/plugin-vue";

import nodePolyfills from "vite-plugin-node-stdlib-browser";
import rollupNodePolyFill from "rollup-plugin-node-polyfills";

// https://vitejs.dev/config/
export default defineConfig(({ command, mode, ssrBuild }) => {
	if (mode === "test") {
		return {
			plugins: [Vue()],
			base: "/openWB/web/display/themes/cards/",
			resolve: {
				alias: {
					"@": fileURLToPath(new URL("./src", import.meta.url)),
				},
			},
			test: {
				globals: true,
				environment: "jsdom",
			},
		};
	} else {
		return {
			plugins: [Vue(), nodePolyfills()],
			base: "/openWB/web/display/themes/cards/",
			resolve: {
				alias: {
					"@": fileURLToPath(new URL("./src", import.meta.url)),
				},
			},
			server: {
				proxy: {
					"/ws": {
						target: "ws://localhost:9001",
						ws: true,
					},
				},
			},
			build: {
				rollupOptions: {
					plugins: [rollupNodePolyFill()],
					output: {
						manualChunks(id) {
							if (id.includes("node_modules")) {
								if (id.includes("inkline")) {
									return "vendor-inkline";
								}
								if (id.includes("fortawesome")) {
									return "vendor-fortawesome";
								}
								return "vendor";
							}
						},
					},
				},
			},
		}
	}
});
