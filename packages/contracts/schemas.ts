/**
 * Zod schemas for API validation
 * 
 * These schemas are used for runtime validation of API requests and responses.
 * They should match the Django backend serializers.
 */

import { z } from "zod";

// Example schemas - add more as Django API is documented
export const clientIdSchema = z.string().min(1);
export const projectIdSchema = z.string().min(1);
