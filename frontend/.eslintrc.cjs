/**
 * ESLint configuration for the React + TypeScript frontend.
 *
 * WHY: Provide a minimal, explicit lint baseline so pre-commit can enforce
 *      consistency and catch obvious issues before CI.
 */
module.exports = {
  root: true,
  env: {
    browser: true,
    es2021: true,
  },
  parser: "@typescript-eslint/parser",
  parserOptions: {
    ecmaVersion: "latest",
    sourceType: "module",
    ecmaFeatures: {
      jsx: true,
    },
  },
  plugins: ["@typescript-eslint", "react", "react-hooks"],
  extends: [
    "eslint:recommended",
    "plugin:react/recommended",
    "plugin:react-hooks/recommended",
    "plugin:@typescript-eslint/recommended",
  ],
  settings: {
    react: {
      version: "detect",
    },
  },
  rules: {
    "react/react-in-jsx-scope": "off",
    // Re-enabled as "warn" - we fixed all API layer any types (Task 3)
    "@typescript-eslint/no-explicit-any": "warn",
    // Re-enabled as "warn" - helps catch unused variables
    "@typescript-eslint/no-unused-vars": ["warn", { 
      "argsIgnorePattern": "^_",
      "varsIgnorePattern": "^_"
    }],
    "react/no-unescaped-entities": "off",
    // Re-enabled as "warn" - helps catch missing dependencies
    "react-hooks/exhaustive-deps": "warn",
  },
  ignorePatterns: ["dist/", "node_modules/"],
};
