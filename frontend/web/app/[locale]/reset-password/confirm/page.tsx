import { PasswordResetConfirmForm } from "@/components/auth/password-reset-confirm-form";

/**
 * Strona ustawienia nowego hasła kodem pod prefiksem języka.
 *
 * Plik trasy tylko komponuje sekcję i layout — żadnych wywołań API ani logiki.
 */
export default function PasswordResetConfirmPage() {
  return (
    <main className="mx-auto w-full max-w-md px-6 py-16">
      <PasswordResetConfirmForm />
    </main>
  );
}
