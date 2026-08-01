import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    environment: 'jsdom',
    setupFiles: ['./vitest.setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text'],
      include: ['src/**/*.ts', 'src/**/*.tsx'],
      exclude: ['src/app/layout.tsx'],
      thresholds: { lines: 90, functions: 90, branches: 80, statements: 90 },
    },
  },
});
