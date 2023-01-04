import { fileURLToPath, URL } from "node:url";

import { defineConfig } from "vite";
import Vue from "@vitejs/plugin-vue";

import nodePolyfills from "vite-plugin-node-stdlib-browser";
import rollupNodePolyFill from "rollup-plugin-node-polyfills";

// https://vitejs.dev/config/
export default defineConfig(({ command, mode }) => {
  var myConfiguration = {
    plugins: [Vue()],
    base: "/openWB/web/display/themes/cards/",
    resolve: {
      alias: {
        "@": fileURLToPath(new URL("./src", import.meta.url)),
      },
    },
  };
  if (command === "serve") {
    if (mode === "test") {
      myConfiguration["test"] = {
        globals: true,
        environment: "jsdom",
      };
    } else {
      myConfiguration.plugins.push(nodePolyfills());
      myConfiguration.server = {
        proxy: {
          "/ws": {
            target: "ws://localhost:9001",
            ws: true,
          },
        },
      };
    }
  } else {
    myConfiguration.plugins.push(nodePolyfills());
    myConfiguration.build = {
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
    };
  }
  return myConfiguration;
});
