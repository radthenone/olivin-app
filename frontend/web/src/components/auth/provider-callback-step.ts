import type { AuthState } from "@olivin/features/auth";

export type ProviderCallbackStep =
  "wait" | "error" | "mfa" | "verify_email" | "signup" | "home" | "failed";

/**
 * Krok strony powrotu od Google/Facebook (#355).
 *
 * Błąd od dostawcy wygrywa z sesją, bo przy anulowaniu sesja wygląda na
 * oczekującą. Pozostałe kroki wynikają ze statusu allauth.
 */
export function providerCallbackStep({
  error,
  isChecking,
  status,
}: {
  error: string | null;
  isChecking: boolean;
  status: AuthState["status"];
}): ProviderCallbackStep {
  if (error) return "error";
  if (isChecking) return "wait";

  switch (status) {
    case "mfa_required":
      return "mfa";
    case "email_verification_required":
      return "verify_email";
    case "authenticated":
      return "home";
    case "provider_signup_required":
      return "signup";
    default:
      return "failed";
  }
}
