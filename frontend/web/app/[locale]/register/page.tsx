import { RegisterForm } from "@/components/auth/register-form";

/**
 * Strona rejestracji pod prefiksem języka.
 *
 * Plik trasy tylko komponuje sekcję i layout — żadnych wywołań API ani logiki.
 */
export default function RegisterPage() {
  return (
    <main className="mx-auto w-full max-w-md px-6 py-16">
      <RegisterForm />
    </main>
  );
}
