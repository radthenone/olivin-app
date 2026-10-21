import { VerifyEmailForm } from "@/components/auth/verify-email-form";

/**
 * Strona potwierdzenia e-maila kodem pod prefiksem języka.
 *
 * Plik trasy tylko komponuje sekcję i layout — żadnych wywołań API ani logiki.
 */
export default function VerifyEmailPage() {
  return (
    <main className="mx-auto w-full max-w-md px-6 py-16">
      <VerifyEmailForm />
    </main>
  );
}
