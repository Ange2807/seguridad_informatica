import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:3000', // Apunta al backend local si corre por fuera de Docker, o cambia al host apropiado
        changeOrigin: true,
        secure: false,
      }
    }
  }
})
