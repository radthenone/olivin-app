import { ENV } from "@core/config/env";

type LogPayload = Record<string, unknown> | unknown;

function write(
  level: "info" | "warn" | "error",
  message: string,
  payload?: LogPayload,
): void {
  if (!ENV.IS_DEV) {
    return;
  }

  const logger = console[level];

  if (payload === undefined) {
    logger(message);
    return;
  }

  logger(message, payload);
}

/**
 * Mały logger developerski bez zależności zewnętrznych.
 *
 * Dlaczego istnieje:
 * warstwa core potrzebuje technicznych logów w development,
 * ale logger nie powinien wymuszać axiosa ani innych peer dependencies.
 */
export const log = {
  info(message: string, payload?: LogPayload): void {
    write("info", message, payload);
  },

  warn(message: string, payload?: LogPayload): void {
    write("warn", message, payload);
  },

  error(message: string, payload?: LogPayload): void {
    write("error", message, payload);
  },
};
