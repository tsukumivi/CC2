import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,
    proxy: { '/api': 'http://127.0.0.1:8000' },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          const normalized = id.replaceAll('\\', '/')
          if (normalized.includes('/node_modules/.pnpm/@codemirror+') || normalized.includes('/node_modules/.pnpm/@lezer+') || normalized.includes('/node_modules/.pnpm/codemirror@')) return 'codemirror'
        },
      },
    },
  },
})
