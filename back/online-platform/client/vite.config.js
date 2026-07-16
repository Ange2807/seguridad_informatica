import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: "../public",
    emptyOutDir: true,
  },
  server: {
    // Dev only: apunta directo a proxy2 (expón su puerto localmente si lo necesitas).
    // En producción, proxy1 ya enruta /api/ al gateway antes de llegar aquí.
    proxy: {
      "/api": "http://localhost:4000",
    },
  },
});
