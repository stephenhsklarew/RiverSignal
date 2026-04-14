import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 180000,
  use: {
    video: 'off',
    launchOptions: { slowMo: 100 },
  },
  projects: [
    {
      name: 'default',
      use: { browserName: 'chromium' },
    },
  ],
});
