/**
 * Pack Logger - Entry point
 */
export { PackLogger, createLogger } from "./logger";
export type { LogLevel, LogData, ApiRequestData, ApiResponseData } from "./logger";

// Export default instance
import { createLogger } from "./logger";
export const log = createLogger("pack", true);
