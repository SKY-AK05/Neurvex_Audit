import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      // Forward all /api/* calls to the Azure Functions local host
      "/api": {
        target: "http://localhost:7071",
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
