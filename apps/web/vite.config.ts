import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@os/ui': path.resolve(__dirname, '../../packages/ui/src'),
      '@os/utils': path.resolve(__dirname, '../../packages/utils/src'),
      '@os/contracts': path.resolve(__dirname, '../../packages/contracts'),
      '@os/api-sdk': path.resolve(__dirname, '../../packages/api-sdk/src'),
    },
  },
  server: {
    port: 5173,
    host: true,
  },
  build: {
    outDir: 'dist',
  },
})
