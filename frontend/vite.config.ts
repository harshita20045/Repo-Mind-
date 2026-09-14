/// <reference types="vitest" />
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    open: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/auth': 'http://localhost:8000',
    },
  },
  build: {
    outDir: '../backend/static', // optional: serve via FastAPI static files later
    emptyOutDir: true,
  },
  test: {
    globals: true,
    environment: 'jsdom',
  },
});
