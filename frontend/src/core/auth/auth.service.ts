/**
 * auth.service.ts
 *
 * Niskopoziomowa warstwa komunikacji z allauth.headless API.
 * Każda funkcja zwraca surową odpowiedź allauth (meta + ewentualne flows):
 *   - 200 → AuthenticatedResponse
 *   - 401 → AuthenticationResponse (z `data.flows`)
 *   - 410 → null (sesja/token nieważne; dotyczy klienta `app`)
 *   - throw → błąd sieciowy / walidacyjny (propagowany wyżej)
 */
import {
  postAllauthClientV1AuthLogin,
  postAllauthClientV1AuthSignup,
  postAllauthClientV1AuthEmailVerify,
  postAllauthClientV1AuthEmailVerifyResend,
  postAllauthClientV1AuthReauthenticate,
} from "@api/generated/auth/authentication-account/authentication-account";
import { postAllauthClientV1Auth2faAuthenticate } from "@api/generated/auth/authentication-2fa/authentication-2fa";
import {
  getAllauthClientV1AuthSession,
  deleteAllauthClientV1AuthSession,
} from "@api/generated/auth/authentication-current-session/authentication-current-session";
import { postAllauthClientV1AccountPasswordChange } from "@api/generated/auth/account-password/account-password";
import {
  postAllauthClientV1AuthPasswordRequest,
  postAllauthClientV1AuthPasswordReset,
} from "@api/generated/auth/authentication-password-reset/authentication-password-reset";
import type {
  LoginBody,
  SignupBody,
  VerifyEmailBody,
  ReauthenticateBody,
} from "@api/generated/auth/schemas";
import { accountsProfileCreate } from "@api/generated/apps/profiles/profiles";
import { accountsAddressesCreate } from "@api/generated/apps/addresses/addresses";
import { authStorage } from "./auth.storage";
import type {
  AllauthClient,
  AuthSessionResponse,
  RegisterPayload,
  ChangePasswordPayload,
  RequestPasswordResetPayload,
  ConfirmPasswordResetPayload,
} from "./auth.types";
import { CONFIG } from "@core/env";

// ─── Pomocniki ────────────────────────────────────────────────────────────────

/** Parsuje i persystuje session_token z metadanych allauth (tylko native). */
async function persistSessionToken(meta: unknown): Promise<void> {
  const token =
    (meta as any)?.sessiontoken ??
    (meta as any)?.session_token ??
    (meta as any)?.sessionToken;
  if (typeof token === "string") {
    await authStorage.setSessionToken(token);
  }
}

async function normalizeAuthResponse<T>(
  promise: Promise<T>,
): Promise<AuthSessionResponse | null> {
  try {
    const res = await promise;
    await persistSessionToken((res as any)?.meta);
    return res as any;
  } catch (error) {
    const response = (error as any)?.response;
    const status: number | undefined = response?.status;
    const data = response?.data;

    if (status === 401) {
      await persistSessionToken(data?.meta);
      return data as any;
    }

    if (status === 410) {
      await authStorage.removeSessionToken();
      return null;
    }

    throw error;
  }
}

// ─── Operacje auth ────────────────────────────────────────────────────────────

/**
 * Logowanie (email + hasło).
 */
export async function login(
  credentials: LoginBody,
  client: AllauthClient = CONFIG.CLIENT,
): Promise<AuthSessionResponse | null> {
  return normalizeAuthResponse(
    postAllauthClientV1AuthLogin(client, credentials),
  );
}

/**
 * Wylogowanie — czyści session token i unieważnia sesję na backendzie.
 */
export async function logout(
  client: AllauthClient = CONFIG.CLIENT,
): Promise<void> {
  try {
    await deleteAllauthClientV1AuthSession(client);
  } finally {
    await authStorage.removeSessionToken();
  }
}

/**
 * Pobiera bieżący stan sesji.
 */
export async function getSession(
  client: AllauthClient = CONFIG.CLIENT,
): Promise<AuthSessionResponse | null> {
  return normalizeAuthResponse(getAllauthClientV1AuthSession(client));
}

/**
 * Rejestracja z fork-join:
 * 1. allauth signup (email + hasło)
 * 2. Równolegle (po udanym signup):
 *    - PATCH profilu (jeśli podano `profile`)
 *    - POST adresu  (jeśli podano `address`)
 *
 * Fork-join jest best-effort — błędy profilu/adresu nie blokują rejestracji.
 * Konto jest zawsze tworzone nawet gdy zapis profilu/ adresu się nie powiedzie.
 */
export async function register(
  payload: RegisterPayload,
  client: AllauthClient = CONFIG.CLIENT,
): Promise<AuthSessionResponse | null> {
  const { email, password, profile, address } = payload;

  const signupBody = { email, password } as unknown as SignupBody;
  const session = await normalizeAuthResponse(
    postAllauthClientV1AuthSignup(client, signupBody),
  );

  // Fork-join — równoległy zapis profilu i adresu
  const forks: Promise<unknown>[] = [];

  if (profile && hasValues(profile)) {
    forks.push(
      accountsProfileCreate({
        firstName: profile.firstName,
        lastName: profile.lastName,
        dateOfBirth: profile.dateOfBirth,
        phoneNumber: profile.phoneNumber,
      } as any).catch((e: unknown) => {
        console.warn("[auth.service] Nie udało się zapisać profilu:", e);
      }),
    );
  }

  if (address && hasValues(address)) {
    forks.push(
      accountsAddressesCreate({
        street: address.street,
        street2: address.street2,
        city: address.city,
        state: address.state,
        postalCode: address.postalCode,
        country: address.country as any,
        isDefault: address.isDefault ?? true,
      } as any).catch((e: unknown) => {
        console.warn("[auth.service] Nie udało się zapisać adresu:", e);
      }),
    );
  }

  if (forks.length > 0) {
    await Promise.allSettled(forks);
  }

  return session;
}

/** Guard — sprawdza, czy obiekt zawiera choć jedno niepuste pole. */
function hasValues(obj: unknown): boolean {
  return Object.values(obj as Record<string, unknown>).some(
    (v) => v !== undefined && v !== null && v !== "",
  );
}

/**
 * Weryfikacja e-mail (po rejestracji lub po kliknięciu linku).
 */
export async function verifyEmail(
  body: VerifyEmailBody,
  client: AllauthClient = CONFIG.CLIENT,
): Promise<AuthSessionResponse | null> {
  return normalizeAuthResponse(
    postAllauthClientV1AuthEmailVerify(client, body),
  );
}

/**
 * Ponowne wysłanie kodu weryfikacyjnego e-mail.
 */
export async function resendEmailVerification(
  client: AllauthClient = CONFIG.CLIENT,
): Promise<void> {
  await postAllauthClientV1AuthEmailVerifyResend(client);
}

/**
 * Weryfikacja MFA (TOTP lub kod recovery).
 */
export async function verifyMfa(
  code: string,
  client: AllauthClient = CONFIG.CLIENT,
): Promise<AuthSessionResponse | null> {
  return normalizeAuthResponse(
    postAllauthClientV1Auth2faAuthenticate(client, { code }),
  );
}

/**
 * Re-autentykacja (np. przed wrażliwą operacją).
 */
export async function reauthenticate(
  body: ReauthenticateBody,
  client: AllauthClient = CONFIG.CLIENT,
): Promise<AuthSessionResponse | null> {
  return normalizeAuthResponse(
    postAllauthClientV1AuthReauthenticate(client, body),
  );
}

/**
 * Zmiana hasła (zalogowany użytkownik zna swoje aktualne hasło).
 */
export async function changePassword(
  payload: ChangePasswordPayload,
  client: AllauthClient = CONFIG.CLIENT,
): Promise<void> {
  await postAllauthClientV1AccountPasswordChange(client, {
    current_password: payload.currentPassword,
    new_password: payload.newPassword,
  });
}

/**
 * Żądanie resetu hasła (bez logowania — wysyła e-mail z linkiem/kodem).
 */
export async function requestPasswordReset(
  payload: RequestPasswordResetPayload,
  client: AllauthClient = CONFIG.CLIENT,
): Promise<void> {
  await postAllauthClientV1AuthPasswordRequest(client, {
    email: payload.email,
  });
}

/**
 * Potwierdzenie resetu hasła (klucz z e-maila + nowe hasło).
 */
export async function confirmPasswordReset(
  payload: ConfirmPasswordResetPayload,
  client: AllauthClient = CONFIG.CLIENT,
): Promise<AuthSessionResponse | null> {
  return normalizeAuthResponse(
    postAllauthClientV1AuthPasswordReset(client, {
      key: payload.key,
      password: payload.password,
    }),
  );
}
