import { PasswordResetRequestForm } from "@/components/auth/password-reset-request-form";

/**
 * Strona prośby o reset hasła pod prefiksem języka.
 *
 * Plik trasy tylko komponuje sekcję i layout — żadnych wywołań API ani logiki.
 */
export default function PasswordResetPage() {
  return (
    <main className="mx-auto w-full max-w-md px-6 py-16">
      <PasswordResetRequestForm />
    </main>
  );
}
