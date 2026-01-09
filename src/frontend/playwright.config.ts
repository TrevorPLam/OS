import { defineConfig } from '@playwright/test'

const isCI =
  process.env.CI === '1' || process.env.CI === 'true' || process.env.E2E_CI === '1'

const baseURL = process.env.E2E_BASE_URL
if (isCI && !baseURL) {
  throw new Error('E2E_BASE_URL must be set when running Playwright in CI mode.')
}

const retries = Number.parseInt(process.env.E2E_RETRIES ?? '', 10)
const resolvedRetries = Number.isNaN(retries) ? (isCI ? 2 : 0) : retries
const trace = process.env.E2E_TRACE ?? (resolvedRetries > 0 ? 'on-first-retry' : 'off')
const video = process.env.E2E_VIDEO ?? 'retain-on-failure'
const screenshot = process.env.E2E_SCREENSHOT ?? 'only-on-failure'
const outputDir = process.env.E2E_OUTPUT_DIR ?? 'test-results'
const reportDir = process.env.E2E_REPORT_DIR ?? 'playwright-report'

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  expect: {
    timeout: 5_000,
  },
  retries: resolvedRetries,
  outputDir,
  preserveOutput: 'failures-only',
  reporter: isCI
    ? [['list'], ['html', { open: 'never', outputFolder: reportDir }]]
    : [['list']],
  use: {
    baseURL: baseURL ?? 'http://localhost:5173',
    screenshot,
    trace,
    video,
  },
})
