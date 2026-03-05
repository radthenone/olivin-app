export type AuthStatus =
  | "idle"
  | "unauthenticated"
  | "authenticated"
  | "pending_mfa"
  | "pending_mfa_setup"
  | "pending_verification";

export type MfaMethod = "totp" | "recovery_codes" | "webauthn";

// Flows zwracane przez allauth w meta.flows
export type AuthFlowId =
  | "login"
  | "signup"
  | "provider_redirect"
  | "provider_token"
  | "provider_signup"
  | "login_by_code"
  | "verify_email"
  | "mfa_authenticate"
  | "mfa_reauthenticate"
  | "mfa_trust"
  | "reauthenticate"
  | (string & {});

export interface AuthFlow {
  id: AuthFlowId;
  [key: string]: unknown;
}

export type AllauthClient = "app" | "browser";

export interface AuthState {
  status: AuthStatus;
  sessionToken: string | null;
  pendingMfaMethods: MfaMethod[];
}
