/**
 * Kształt odpowiedzi allauth, zanim UI zobaczy statusy HTTP.
 *
 * `isAllauthBody` jest granicą na odpowiedzi z backendu — dalej nie
 * przepuszczamy `any` do rdzenia auth.
 */

export type AuthFlow = {
  id: string;
  providers?: string[];
  is_pending?: boolean;
};

export type AllauthUser = {
  id: number;
  display: string;
  email: string;
  has_usable_password: boolean;
};

export type AllauthBody = {
  status: number;
  data?: {
    user?: AllauthUser;
    flows?: AuthFlow[];
    methods?: unknown[];
  };
  meta: {
    is_authenticated: boolean;
    session_token?: string;
  };
};

export type AuthState =
  | { status: "authenticated"; user: AllauthUser; flows: AuthFlow[] }
  | { status: "unauthenticated"; flows: AuthFlow[] }
  | { status: "mfa_required"; flows: AuthFlow[] }
  | { status: "email_verification_required"; flows: AuthFlow[] }
  | { status: "provider_signup_required"; flows: AuthFlow[] };

/**
 * Sprawdza, czy nieznana odpowiedź wygląda jak body allauth.
 */
export function isAllauthBody(value: unknown): value is AllauthBody {
  if (!value || typeof value !== "object") return false;

  const body = value as Record<string, unknown>;
  const meta = body.meta as Record<string, unknown> | undefined;

  return (
    typeof body.status === "number" &&
    !!meta &&
    typeof meta.is_authenticated === "boolean"
  );
}
