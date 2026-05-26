import { allauthClient } from "@core/config/platform";
import type { HttpResponse } from "@core/http/types";
import { sessionTokenStorage } from "./session-token.storage";
import { isAllauthBody } from "./auth.types";

/**
 * Obsługuje skutki uboczne odpowiedzi allauth.
 *
 * Dlaczego istnieje:
 * transport HTTP nie powinien wiedzieć, czym jest allauth,
 * ale po loginie app musi zapisać meta.session_token do SecureStore.
 */
export async function handleAllauthSessionLifecycle(
  response: HttpResponse<unknown>,
): Promise<void> {
  if (allauthClient !== "app") return;

  if (response.status === 410) {
    await sessionTokenStorage.remove();
    return;
  }

  if (!isAllauthBody(response.data)) return;

  const token = response.data.meta.session_token;
  if (token) {
    await sessionTokenStorage.set(token);
  }
}
