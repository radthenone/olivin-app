import { useSession } from "./use-session";

/**
 * Zamienia surowe query sesji na flagi wygodne dla UI i routingu.
 */
export function useAuth() {
  const session = useSession();
  const status = session.data?.status;

  return {
    session,
    status,
    isChecking: session.isLoading,
    isAuthenticated: status === "authenticated",
    isUnauthenticated: status === "unauthenticated",
    isMfaRequired: status === "mfa_required",
    isEmailVerificationRequired: status === "email_verification_required",
    user: status === "authenticated" ? session.data?.user : null,
    flows: session.data?.flows ?? [],
  };
}
