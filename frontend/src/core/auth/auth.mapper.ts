import type { AuthFlow, AuthState } from "./auth.types";
import { isAllauthBody } from "./auth.types";

/**
 * Mapuje odpowiedź allauth na prosty stan aplikacji.
 *
 * Dlaczego istnieje:
 * UI i routing nie powinny znać statusów 401/410, meta ani flows allauth.
 */
export function mapAllauthBodyToAuthState(body: unknown): AuthState {
  if (!isAllauthBody(body)) {
    return { status: "unauthenticated", flows: [] };
  }

  const flows = body.data?.flows ?? [];

  if (body.meta.is_authenticated && body.data?.user) {
    return {
      status: "authenticated",
      user: body.data.user,
      flows,
    };
  }

  if (hasFlow(flows, "mfa_authenticate")) {
    return { status: "mfa_required", flows };
  }

  if (hasFlow(flows, "verify_email")) {
    return { status: "email_verification_required", flows };
  }

  return { status: "unauthenticated", flows };
}

function hasFlow(flows: AuthFlow[], id: string) {
  return flows.some((flow) => flow.id === id);
}
