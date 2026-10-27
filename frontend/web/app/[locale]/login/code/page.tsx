import { LoginCodeRequestForm } from "@/components/auth/login-code-request-form";

/**
 * Strona zamówienia jednorazowego kodu logowania pod prefiksem języka.
 *
 * Plik trasy tylko komponuje sekcję i layout — żadnych wywołań API ani logiki.
 */
export default function LoginCodePage() {
  return (
    <main className="mx-auto w-full max-w-md px-6 py-16">
      <LoginCodeRequestForm />
    </main>
  );
}
