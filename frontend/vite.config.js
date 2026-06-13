import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// API/media proxy target. Local dev → localhost; in Docker we pass
// VITE_API_PROXY=http://backend:8000 so the dev server can reach the API service.
const proxyTarget = process.env.VITE_API_PROXY || "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true, // listen on 0.0.0.0 so the container is reachable
    watch: {
      // Bind-mounted source on Windows/Docker needs polling for HMR to fire.
      usePolling: process.env.CHOKIDAR_USEPOLLING === "true",
    },
    proxy: {
      "/api": proxyTarget,
      "/media": proxyTarget,
    },
  },
});
