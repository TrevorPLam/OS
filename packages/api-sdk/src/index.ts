/**
 * API SDK Package
 * 
 * This package contains generated API clients from OpenAPI specs and manual extensions.
 * 
 * Structure:
 * - src/generated/ - Auto-generated code from OpenAPI specs (do not edit manually)
 * - src/manual/ - Manual extensions and custom client code
 * 
 * Note: Generated and manual directories will be created when code generation is run.
 * For now, this package exports contracts to prevent build errors.
 */

// Re-export contracts for convenience
export * from "@os/contracts";

// TODO: Uncomment when code generation is set up
// export * from './generated';
// export * from './manual';
