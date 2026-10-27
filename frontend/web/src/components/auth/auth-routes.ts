import type { Route } from "next";

import {
  LOGIN_CODE_EXPIRED_PARAM,
  LOGIN_CODE_EXPIRED_VALUE,
} from "./login-code-expired";

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
  loginCodeExpired: (locale: string) =>
    `/${locale}/login/code?${LOGIN_CODE_EXPIRED_PARAM}=${LOGIN_CODE_EXPIRED_VALUE}` as Route,
};
