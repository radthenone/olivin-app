"use client";

import Link from "next/link";
import type { Route } from "next";
import { useLocale, useTranslations } from "next-intl";

import { Card, CardContent } from "@/components/ui/card";

/**
 * Komunikat o nieudanym powrocie od dostawcy z linkiem do logowania (#355).
 *
 * Wspólny dla błędu od dostawcy, braku danych konta i wygaśnięcia MFA.
 */
export function ProviderCallbackMessage({ message }: { message: string }) {
  const t = useTranslations("auth");
  const locale = useLocale();

  return (
    <Card>
      <CardContent className="flex flex-col gap-4 pt-6">
        <p className="text-sm text-destructive" role="alert">
          {message}
        </p>
        <Link
          className="underline underline-offset-4"
          href={`/${locale}/login` as Route}
        >
          {t("provider.backToLogin")}
        </Link>
      </CardContent>
    </Card>
  );
}
