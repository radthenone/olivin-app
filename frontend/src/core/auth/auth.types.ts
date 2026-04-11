import type { AuthenticatedResponse } from "@api/generated/auth/schemas/authenticatedResponse";
import type { AuthenticationResponse } from "@api/generated/auth/schemas/authenticationResponse";

// ─── MFA ────────────────────────────────────────────────────────────────────
export type MfaMethod = "totp" | "recovery_codes" | "webauthn";

// ─── Allauth Flows ───────────────────────────────────────────────────────────
export type AuthFlowId =
  | "login"
  | "signup"
  | "provider_redirect"
  | "provider_token"
  | "provider_signup"
  | "login_by_code"
  | "verify_email"
  | "verify_phone"
  | "mfa_authenticate"
  | "mfa_reauthenticate"
  | "mfa_trust"
  | "reauthenticate"
  | (string & {});

export interface AuthFlow {
  id: AuthFlowId;
  [key: string]: unknown;
}

// ─── Typ klienta allauth ─────────────────────────────────────────────────────
export type AllauthClient = "app" | "browser";

// ─── Odpowiedź session (raw) ────────────────────────────────────────────────
export type AuthSessionResponse =
  | AuthenticatedResponse
  | AuthenticationResponse;

/**
 * `undefined` → jeszcze nie sprawdzono sesji
 * `null`      → sprawdzono, ale brak ważnej sesji (np. 410 / wylogowany)
 */
export type AuthSessionState = AuthSessionResponse | null | undefined;

// ─── Stan globalny auth ──────────────────────────────────────────────────────
export interface AuthState {
  session: AuthSessionState;
}

// ─── Dane logowania ──────────────────────────────────────────────────────────
export interface LoginCredentials {
  email: string;
  password: string;
}

// ─── Dane rejestracji ────────────────────────────────────────────────────────
export interface RegisterProfileData {
  firstName?: string;
  lastName?: string;
  dateOfBirth?: string | null;
  phoneNumber?: string;
}

export interface RegisterAddressData {
  street?: string;
  street2?: string;
  city?: string;
  state?: string;
  postalCode?: string;
  country?: string;
  isDefault?: boolean;
}

/**
 * Kompletne dane rejestracji: allauth signup + opcjonalny profil + opcjonalny adres.
 *
 * Uwaga: allauth SignupBody używa pojedynczego pola `password` (nie password1/password2).
 * Walidacja potwierdzenia hasła powinna odbyć się po stronie UI.
 */
export interface RegisterPayload {
  // allauth fields
  email: string;
  password: string;
  // fork-join profile (opcjonalne pola po stronie API są optional)
  profile?: RegisterProfileData;
  // fork-join address (całość opcjonalna)
  address?: RegisterAddressData;
}

// ─── Zmiana hasła ────────────────────────────────────────────────────────────
export interface ChangePasswordPayload {
  currentPassword: string;
  newPassword: string;
  newPasswordConfirm: string;
}

// ─── Reset hasła ─────────────────────────────────────────────────────────────
export interface RequestPasswordResetPayload {
  email: string;
}

export interface ConfirmPasswordResetPayload {
  /** Klucz z e-maila resetującego hasło */
  key: string;
  /** Nowe hasło */
  password: string;
}
