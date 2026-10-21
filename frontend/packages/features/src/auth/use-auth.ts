import { useSession } from "./use-session";

/**
 * Zamienia stan sesji na flagi wygodne dla UI i routingu.
 *
 * Expo Router potrzebuje prostych predykatów do ochrony route group, a źródłem
 * prawdy nadal pozostaje endpoint allauth `auth/session`.
 */
export function useAuth() {
  const session = useSession();
  const status = session.state.status;

  return {
    session,
    status,
    isChecking: session.isChecking,
    isAuthenticated: status === "authenticated",
    isUnauthenticated: status === "unauthenticated",
    isMfaRequired: status === "mfa_required",
    isEmailVerificationRequired: status === "email_verification_required",
    isProviderSignupRequired: status === "provider_signup_required",
    user: session.user,
    flows: session.state.flows,
  };
}
