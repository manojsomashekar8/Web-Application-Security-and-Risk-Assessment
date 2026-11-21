import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev only: forward /api to the backend on the host (production uses nginx, see nginx.conf).
export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/api": "http://127.0.0.1:8080" } },
});
