import { getGetAllauthClientV1AuthSessionQueryKey } from "@olivin/api/generated/auth/authentication-current-session/authentication-current-session";

import { getAuthClient } from "./auth-config";

/**
 * Klucz sesji pochodzi z Orvala, więc invalidacja po loginie, logoutcie i
 * każdym kroku auth trafia dokładnie w cache zapytania sesji (ADR 0033).
 */
export function getAuthSessionQueryKey() {
  return getGetAllauthClientV1AuthSessionQueryKey(getAuthClient());
}
