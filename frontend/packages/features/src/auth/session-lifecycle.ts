import { getAuthClient, getSessionTokenStorage } from "./auth-config";
import { isAllauthBody } from "./auth-types";

type AuthHttpResponse = {
  status: number;
  data: unknown;
};

/**
 * Obsługuje skutki uboczne odpowiedzi allauth.
 *
 * Transport nie powinien wiedzieć, gdzie aplikacja trzyma token sesji. Po
 * loginie klient `app` musi zapisać `meta.session_token` przez adapter
 * wstrzyknięty przy starcie, a po 410 usunąć wygasły token.
 *
 * Patrz docs/adr/0006-transport-wstrzykiwany-do-klienta-api.md
 */
export async function handleAllauthSessionLifecycle(
  response: AuthHttpResponse,
): Promise<void> {
  if (getAuthClient() !== "app") return;

  const storage = getSessionTokenStorage();

  if (response.status === 410) {
    await storage.remove();
    return;
  }

  if (!isAllauthBody(response.data)) return;

  const token = response.data.meta.session_token;
  if (token) {
    await storage.set(token);
  }
}
