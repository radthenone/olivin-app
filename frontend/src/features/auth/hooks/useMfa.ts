/**
 * useMfa.ts
 *
 * Hook do obsługi dwuetapowej weryfikacji (TOTP / kody recovery).
 * Używany gdy w raw `session.data.flows` pojawia się flow MFA.
 */
import { useState } from "react";
import { authService, useAuthStore } from "@core/auth";

export interface UseMfaResult {
  verifyMfa: (code: string) => Promise<void>;
  isLoading: boolean;
  error: string | null;
  clearError: () => void;
}

export function useMfa(): UseMfaResult {
  const { setSession } = useAuthStore();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const verifyMfa = async (code: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const session = await authService.verifyMfa(code);
      setSession(session);
    } catch (err: unknown) {
      const message = extractMfaError(err);
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  return {
    verifyMfa,
    isLoading,
    error,
    clearError: () => setError(null),
  };
}

function extractMfaError(err: unknown): string {
  const data = (err as any)?.response?.data;
  if (Array.isArray(data?.errors)) {
    return data.errors.map((e: any) => e.message ?? e).join(", ");
  }
  if (typeof data?.detail === "string") return data.detail;
  if (err instanceof Error) return err.message;
  return "Nieprawidłowy kod. Spróbuj ponownie.";
}
