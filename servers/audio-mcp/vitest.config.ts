import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    include: ['tests/**/*.test.ts'],
    exclude: ['node_modules', 'dist'],
    timeout: 30000,
    setupFiles: []
  },
  resolve: {
    alias: {
      '@vid-ed-x/core': path.resolve(__dirname, '../../packages/core/src')
    }
  }
});
