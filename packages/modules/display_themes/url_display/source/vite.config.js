import { defineConfig } from "vite";
import { nodePolyfills } from "vite-plugin-node-polyfills";
import rollupNodePolyfills from "rollup-plugin-polyfill-node";

export default defineConfig({
  base: "/openWB/web/display/themes/url_display/",
  plugins: [
    nodePolyfills({
      protocolImports: true,
    }),
  ],
  build: {
    rollupOptions: {
      plugins: [rollupNodePolyfills()],
      output: {
        entryFileNames: "assets/index.js",
        chunkFileNames: "assets/[name].js",
        assetFileNames: "assets/[name][extname]",
      },
    },
  },
});
