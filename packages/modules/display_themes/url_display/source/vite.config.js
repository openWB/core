import { defineConfig } from "vite";

export default defineConfig({
  base: "/openWB/web/display/themes/url_display/",
  build: {
    rollupOptions: {
      output: {
        entryFileNames: "assets/index.js",
        chunkFileNames: "assets/[name].js",
        assetFileNames: "assets/[name][extname]",
      },
    },
  },
});
