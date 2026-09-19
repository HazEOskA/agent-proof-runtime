import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The built bundle is served by Agent Proof Runtime at /control-plane/.
// During development Vite proxies the APR endpoints so the browser stays
// same-origin and the runtime keeps its loopback Host check.
const APR_ORIGIN = process.env.APR_ORIGIN ?? "http://127.0.0.1:8080";

export default defineConfig({
  base: "/control-plane/",
  plugins: [react()],
  build: {
    outDir: "dist",
    emptyOutDir: true,
    sourcemap: false,
  },
  server: {
    port: 5173,
    proxy: {
      "/api": { target: APR_ORIGIN, changeOrigin: false },
      "/health": { target: APR_ORIGIN, changeOrigin: false },
      "/runs": { target: APR_ORIGIN, changeOrigin: false },
    },
  },
});
