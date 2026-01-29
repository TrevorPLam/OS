/**
 * Error handling middleware
 */

import type { Request, Response, NextFunction } from "express";
import { logger } from "../utils/logger";

export interface ApiError extends Error {
  statusCode?: number;
  code?: string;
}

export function errorHandler(
  err: ApiError,
  _req: Request,
  res: Response,
  _next: NextFunction,
): void {
  const statusCode = err.statusCode || 500;
  const message = err.message || "Internal Server Error";

  logger.error("Request error", {
    statusCode,
    message,
    code: err.code,
    stack: process.env.NODE_ENV === "development" ? err.stack : undefined,
  });

  res.status(statusCode).json({
    error: {
      message,
      code: err.code || "INTERNAL_ERROR",
      ...(process.env.NODE_ENV === "development" && { stack: err.stack }),
    },
  });
}
