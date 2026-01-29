/**
 * Route registration
 * 
 * This file registers all TypeScript routes for migrated modules.
 * As modules are migrated from Django to TypeScript, add their routes here.
 */

import type { Express } from "express";
import { logger } from "../utils/logger";

/**
 * Register all TypeScript routes
 * 
 * Currently, all routes are proxied to Django.
 * As modules are migrated, add their route handlers here.
 */
export function registerRoutes(app: Express): void {
  logger.info("Registering TypeScript routes");

  // Example: Once a module is migrated, uncomment and implement:
  // app.use("/api/clients", clientsRouter);
  // app.use("/api/projects", projectsRouter);

  // For now, all routes are handled by the Django proxy
  logger.info("All routes currently proxied to Django backend");
}
