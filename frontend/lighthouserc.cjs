/**
 * Lighthouse CI configuration for the Vite frontend.
 *
 * Document Type: Config
 * Last Updated: 2026-01-16
 *
 * Why this file exists:
 * - Keeps performance checks reproducible across local runs and CI.
 * - Documents the exact URLs and build artifacts LHCI should inspect.
 *
 * How to use:
 * 1) npm run build
 * 2) npm run lighthouse:ci
 *
 * Notes:
 * - staticDistDir lets LHCI serve the built assets locally without
 *   needing a separate preview server.
 * - Assertions are warnings today to avoid blocking early iterations;
 *   raise thresholds once a stable baseline is established.
 */
module.exports = {
  ci: {
    collect: {
      staticDistDir: './dist',
      url: ['http://localhost/'],
      numberOfRuns: 3,
      settings: {
        preset: 'desktop',
      },
    },
    assert: {
      preset: 'lighthouse:recommended',
      assertions: {
        'categories:performance': ['warn', { minScore: 0.6 }],
        'categories:accessibility': ['warn', { minScore: 0.8 }],
        'categories:best-practices': ['warn', { minScore: 0.8 }],
        'categories:seo': ['warn', { minScore: 0.8 }],
      },
    },
    upload: {
      target: 'temporary-public-storage',
    },
  },
}
