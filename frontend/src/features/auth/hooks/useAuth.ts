/**
 * useAuth.ts
 *
 * Główny hook eksponujący stan auth do komponentów.
 * Łączy authStore z wygodnymi selektorami.
 *
 * Użycie w komponencie:
 *   const { session, isAuthenticated, flows } = useAuth();
 */
import { useAuthStore } from "@core/auth";
import type { AuthFlow, AuthSessionResponse } from "@core/auth";

export function useAuth() {
  const session = useAuthStore((s) => s.session);

  const isSessionChecked = session !== undefined;
  const isAuthenticated = session?.meta?.is_authenticated === true;

  const rawFlows = extractFlowsFromSession(session ?? undefined);
  const flows = isAuthenticated ? [] : rawFlows;
  const flowIds = flows.map((f) => f.id);

  const isPendingMfa =
    flowIds.includes("mfa_authenticate") ||
    flowIds.includes("mfa_reauthenticate");
  const isPendingVerification =
    flowIds.includes("verify_email") || flowIds.includes("verify_phone");
  const isPendingMfaSetup = flowIds.includes("mfa_trust");

  return {
    // Raw
    session,
    flows,

    // Flagi
    isSessionChecked,
    isSessionChecking: session === undefined,
    isAuthenticated,
    isUnauthenticated: isSessionChecked && !isAuthenticated,
    isPendingMfa,
    isPendingMfaSetup,
    isPendingVerification,

    // Pomocnicze
    hasAnyPendingFlow: flows.length > 0,
    pendingFlowIds: flowIds,
  };
}

function extractFlowsFromSession(
  session: AuthSessionResponse | null | undefined,
): AuthFlow[] {
  const maybeFlows = (session as any)?.data?.flows;
  return (Array.isArray(maybeFlows) ? maybeFlows : []) as AuthFlow[];
}
