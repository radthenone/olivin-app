export type AuthFlow = {
  id: string;
  providers?: string[];
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
  | { status: "email_verification_required"; flows: AuthFlow[] };

/**
 * Sprawdza, czy nieznana odpowiedź wygląda jak body allauth.
 *
 * Dlaczego istnieje:
 * granica z backendem nie powinna przepuszczać `any` do rdzenia auth.
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
