"use client";

import { useEffect, useState } from "react";
import { useLocale, useTranslations } from "next-intl";

import { getGetAllauthClientV1AuthSessionUrl } from "@olivin/api/generated/auth/authentication-current-session/authentication-current-session";

import { Button } from "@/components/ui/button";
import { ensureCsrfToken } from "@/lib/csrf";

const PROVIDERS = [
  { id: "google", labelKey: "continueGoogle" },
  { id: "facebook", labelKey: "continueFacebook" },
] as const;

const REDIRECT_PATH = "/_allauth/browser/v1/auth/provider/redirect";

/**
 * Przyciski logowania przez Google i Facebook (#355).
 *
 * Allauth w trybie przeglądarkowym przyjmuje formularz POST, który sam
 * przekierowuje do dostawcy, więc każdy przycisk to osobny formularz. Token CSRF
 * i adres powrotu znamy dopiero w przeglądarce, dlatego przyciski czekają na
 * pierwszy efekt.
 */
export function ProviderButtons() {
  const t = useTranslations("auth.provider");
  const locale = useLocale();
  const [fields, setFields] = useState<{
    csrfToken: string;
    callbackUrl: string;
  } | null>(null);

  useEffect(() => {
    let cancelled = false;

    void ensureCsrfToken(getGetAllauthClientV1AuthSessionUrl("browser")).then(
      (csrfToken) => {
        if (cancelled || !csrfToken) return;

        setFields({
          csrfToken,
          callbackUrl: `${window.location.origin}/${locale}/auth/provider/callback`,
        });
      },
    );

    return () => {
      cancelled = true;
    };
  }, [locale]);

  return (
    <div className="flex flex-col gap-2">
      {PROVIDERS.map(({ id, labelKey }) => (
        <form action={REDIRECT_PATH} key={id} method="post">
          <input
            name="csrfmiddlewaretoken"
            type="hidden"
            value={fields?.csrfToken ?? ""}
          />
          <input name="provider" type="hidden" value={id} />
          <input name="process" type="hidden" value="login" />
          <input
            name="callback_url"
            type="hidden"
            value={fields?.callbackUrl ?? ""}
          />
          <Button
            className="w-full"
            disabled={!fields}
            type="submit"
            variant="outline"
          >
            {t(labelKey)}
          </Button>
        </form>
      ))}
    </div>
  );
}
