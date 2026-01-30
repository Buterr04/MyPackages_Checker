import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/vision': 'http://127.0.0.1:8000',
      '/vision-assess': 'http://127.0.0.1:8000',
      '/docs': 'http://127.0.0.1:8000',
      '/docs/list': 'http://127.0.0.1:8000',
      '/docs/ingest': 'http://127.0.0.1:8000',
    },
  },
})
