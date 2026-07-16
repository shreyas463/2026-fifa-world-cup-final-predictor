import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// `base` is set for the GitHub Pages build via VITE_BASE (repo sub-path);
// defaults to "/" for local dev and other hosts.
export default defineConfig({
  base: process.env.VITE_BASE ?? "/",
  plugins: [react()],
  server: { port: 5173, proxy: { "/api": "http://localhost:8000" } },
});
