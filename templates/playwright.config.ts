import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  
  use: {
    headless: true,
    baseURL: 'http://localhost:5173',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'retain-on-failure',
  },
  
  webServer: {
    command: 'npm run dev',
    port: 5173,
    reuseExistingServer: false,
    timeout: 120000,
  },
});
