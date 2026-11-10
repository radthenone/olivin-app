import { LoginCodeRequestForm } from "@/components/auth/login-code-request-form";
import {
  LOGIN_CODE_EXPIRED_PARAM,
  loginCodeExpiredReason,
} from "@/components/auth/login-code-expired";

/**
 * Strona zamówienia jednorazowego kodu logowania pod prefiksem języka.
 *
 * Trasa tylko czyta parametr `expired` (ustawiany przez ekran kodu albo MFA,
 * gdy oczekujące logowanie przepadło) i przekazuje powód do formularza; poza
 * tym nie ma tu logiki ani wywołań API.
 */
export default async function LoginCodePage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | undefined>>;
}) {
  const params = await searchParams;
  const expired = loginCodeExpiredReason(params[LOGIN_CODE_EXPIRED_PARAM]);

  return (
    <main className="mx-auto w-full max-w-md px-6 py-16">
      <LoginCodeRequestForm expired={expired} />
    </main>
  );
}
