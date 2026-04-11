/**
 * useEmailVerification.ts
 *
 * Hook do weryfikacji adresu e-mail po rejestracji lub logowaniu.
 */
import { useState } from "react";
import { authService, useAuthStore } from "@core/auth";

export interface UseEmailVerificationResult {
  verifyEmail: (key: string) => Promise<void>;
  resend: () => Promise<void>;
  isVerifying: boolean;
  isResending: boolean;
  error: string | null;
  clearError: () => void;
}

export function useEmailVerification(): UseEmailVerificationResult {
  const { setSession } = useAuthStore();
  const [isVerifying, setIsVerifying] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const verifyEmail = async (key: string) => {
    setIsVerifying(true);
    setError(null);

    try {
      const session = await authService.verifyEmail({ key });
      setSession(session);
    } catch (err: unknown) {
      setError(extractError(err, "Nieprawidłowy kod weryfikacyjny."));
    } finally {
      setIsVerifying(false);
    }
  };

  const resend = async () => {
    setIsResending(true);
    setError(null);
    try {
      await authService.resendEmailVerification();
    } catch (err: unknown) {
      setError(
        extractError(err, "Nie udało się wysłać kodu. Spróbuj ponownie."),
      );
    } finally {
      setIsResending(false);
    }
  };

  return {
    verifyEmail,
    resend,
    isVerifying,
    isResending,
    error,
    clearError: () => setError(null),
  };
}

function extractError(err: unknown, fallback: string): string {
  const data = (err as any)?.response?.data;
  if (Array.isArray(data?.errors)) {
    return data.errors.map((e: any) => e.message ?? e).join(", ");
  }
  if (typeof data?.detail === "string") return data.detail;
  if (err instanceof Error) return err.message;
  return fallback;
}
