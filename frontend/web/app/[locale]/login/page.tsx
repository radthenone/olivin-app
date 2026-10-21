import { LoginForm } from "@/components/auth/login-form";

/**
 * Strona logowania pod prefiksem języka.
 *
 * Plik trasy tylko komponuje sekcję i layout — żadnych wywołań API ani logiki.
 */
export default function LoginPage() {
  return (
    <main className="mx-auto w-full max-w-md px-6 py-16">
      <LoginForm />
    </main>
  );
}
