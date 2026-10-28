import type { Route } from "next";

import {
  LOGIN_CODE_EXPIRED_PARAM,
  loginCodeExpiredValue,
  type LoginCodeExpiredReason,
} from "./login-code-expired";
import { passwordResetExpiredQuery } from "./password-reset-expired";

/**
 * Jedna mapa tras ekranów auth (#406).
 *
 * Każda funkcja dostaje locale i zwraca typowaną ścieżkę Route. Cast jest
 * tylko tutaj, więc formularze nie składają adresów ręcznie.
 */
export const authRoutes = {
  home: (locale: string) => `/${locale}` as Route,
  login: (locale: string) => `/${locale}/login` as Route,
  loginCode: (locale: string) => `/${locale}/login/code` as Route,
  loginCodeConfirm: (locale: string) =>
    `/${locale}/login/code/confirm` as Route,
  loginCodeExpired: (locale: string, reason: LoginCodeExpiredReason = "mfa") =>
    `/${locale}/login/code?${LOGIN_CODE_EXPIRED_PARAM}=${loginCodeExpiredValue(reason)}` as Route,
  passwordReset: (locale: string) => `/${locale}/reset-password` as Route,
  passwordResetConfirm: (locale: string) =>
    `/${locale}/reset-password/confirm` as Route,
  passwordResetExpired: (locale: string) =>
    `/${locale}/reset-password?${passwordResetExpiredQuery()}` as Route,
};
