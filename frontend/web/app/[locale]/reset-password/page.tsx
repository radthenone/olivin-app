import { PasswordResetRequestForm } from "@/components/auth/password-reset-request-form";
import {
  PASSWORD_RESET_EXPIRED_PARAM,
  isPasswordResetExpired,
} from "@/components/auth/password-reset-expired";

/**
 * Strona prośby o reset hasła pod prefiksem języka.
 *
 * Trasa tylko czyta parametr `expired` (ustawiany przez ekran ustawienia hasła,
 * gdy etap resetu przepadł) i przekazuje go do formularza; poza tym nie ma tu
 * logiki ani wywołań API.
 */
export default async function PasswordResetPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | undefined>>;
}) {
  const params = await searchParams;
  const expired = isPasswordResetExpired(params[PASSWORD_RESET_EXPIRED_PARAM]);

  return (
    <main className="mx-auto w-full max-w-md px-6 py-16">
      <PasswordResetRequestForm expired={expired} />
    </main>
  );
}
