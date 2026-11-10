import { Suspense } from "react";

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
 * tym nie ma tu logiki ani wywołań API. `searchParams` czytamy w `<Suspense>`,
 * bo z Cache Components tylko ta część jest dynamiczna (ADR 0034).
 */
export default function LoginCodePage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | undefined>>;
}) {
  return (
    <main className="mx-auto w-full max-w-md px-6 py-16">
      <Suspense fallback={null}>
        <LoginCodeContent searchParams={searchParams} />
      </Suspense>
    </main>
  );
}

async function LoginCodeContent({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | undefined>>;
}) {
  const params = await searchParams;
  const expired = loginCodeExpiredReason(params[LOGIN_CODE_EXPIRED_PARAM]);

  return <LoginCodeRequestForm expired={expired} />;
}
