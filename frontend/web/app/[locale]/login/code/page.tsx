import { LoginCodeRequestForm } from "@/components/auth/login-code-request-form";
import {
  LOGIN_CODE_EXPIRED_PARAM,
  LOGIN_CODE_EXPIRED_VALUE,
} from "@/components/auth/login-code-expired";

/**
 * Strona zamówienia jednorazowego kodu logowania pod prefiksem języka.
 *
 * Trasa tylko czyta parametr `expired` (ustawiany przez ekran MFA po
 * wygaśnięciu logowania) i przekazuje go jako flagę do formularza; poza tym
 * nie ma tu logiki ani wywołań API.
 */
export default async function LoginCodePage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | undefined>>;
}) {
  const params = await searchParams;
  const expired = params[LOGIN_CODE_EXPIRED_PARAM] === LOGIN_CODE_EXPIRED_VALUE;

  return (
    <main className="mx-auto w-full max-w-md px-6 py-16">
      <LoginCodeRequestForm expired={expired} />
    </main>
  );
}
