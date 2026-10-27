import { LoginCodeConfirmForm } from "@/components/auth/login-code-confirm-form";

/**
 * Strona wpisania jednorazowego kodu logowania pod prefiksem języka.
 *
 * Plik trasy tylko komponuje sekcję i layout — żadnych wywołań API ani logiki.
 */
export default function LoginCodeConfirmPage() {
  return (
    <main className="mx-auto w-full max-w-md px-6 py-16">
      <LoginCodeConfirmForm />
    </main>
  );
}
