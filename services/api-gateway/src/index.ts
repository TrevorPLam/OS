/**
 * OS API Gateway
 * 
 * TypeScript gateway that wraps the Django backend.
 * 
 * Strategy:
 * - Initially proxies all requests to Django backend
 * - Gradually migrate modules from Django to TypeScript
 * - Once a module is migrated, route it directly instead of proxying
 * 
 * This follows the FIRST standard: TypeScript-first approach with incremental migration.
 */

import express from "express";
import type { Request, Response, NextFunction } from "express";
import { createProxyMiddleware } from "http-proxy-middleware";
import cors from "cors";
import { logger } from "./utils/logger";
import { errorHandler } from "./middleware/errorHandler";
import { registerRoutes } from "./routes";

const app = express();

// Get Django backend URL from environment
const DJANGO_BACKEND_URL = process.env.DJANGO_BACKEND_URL || "http://localhost:8000";
const GATEWAY_PORT = parseInt(process.env.GATEWAY_PORT || "3000", 10);

// CORS configuration
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(",") || ["http://localhost:5173", "http://localhost:3000"],
  credentials: true,
}));

// Body parsing
app.use(express.json({ limit: "10mb" }));
app.use(express.urlencoded({ extended: true, limit: "10mb" }));

// Request logging
app.use((req: Request, res: Response, next: NextFunction) => {
  const start = Date.now();
  logger.info("Request received", {
    method: req.method,
    path: req.path,
    ip: req.ip,
  });

  res.on("finish", () => {
    const duration = Date.now() - start;
    logger.info("Request completed", {
      method: req.method,
      path: req.path,
      statusCode: res.statusCode,
      duration: `${duration}ms`,
    });
  });

  next();
});

// Health check endpoint
app.get("/health", (_req: Request, res: Response) => {
  res.json({
    status: "ok",
    service: "api-gateway",
    timestamp: new Date().toISOString(),
  });
});

// Register TypeScript routes (for migrated modules)
registerRoutes(app);

// Proxy all other API requests to Django backend
// This will be gradually replaced as modules are migrated
const djangoProxy = createProxyMiddleware({
  target: DJANGO_BACKEND_URL,
  changeOrigin: true,
  pathRewrite: {
    "^/api": "/api", // Keep /api prefix
  },
  onProxyReq: (proxyReq, req) => {
    logger.debug("Proxying to Django", {
      method: req.method,
      path: req.path,
      target: DJANGO_BACKEND_URL,
    });
  },
  onProxyRes: (proxyRes, req) => {
    logger.debug("Django response received", {
      method: req.method,
      path: req.path,
      statusCode: proxyRes.statusCode,
    });
  },
  onError: (err, req) => {
    logger.error("Django proxy error", {
      error: err.message,
      method: req.method,
      path: req.path,
    });
  },
});

// Apply proxy to all /api routes that aren't handled by TypeScript routes
app.use("/api", (req: Request, res: Response, next: NextFunction) => {
  // If the route was handled by TypeScript routes, skip proxying
  if (res.headersSent) {
    return next();
  }
  // Otherwise, proxy to Django
  djangoProxy(req, res, next);
});

// Error handler (must be last)
app.use(errorHandler);

// Start server
app.listen(GATEWAY_PORT, "0.0.0.0", () => {
  logger.info("API Gateway started", {
    port: GATEWAY_PORT,
    djangoBackend: DJANGO_BACKEND_URL,
    environment: process.env.NODE_ENV || "development",
  });
});
