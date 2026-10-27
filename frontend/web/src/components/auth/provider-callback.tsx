"use client";

import Link from "next/link";
import type { Route } from "next";
import { useLocale, useTranslations } from "next-intl";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect } from "react";

import { useSession } from "@olivin/features/auth";

import { providerErrorKey } from "./provider-error-key";
import { ProviderSignupForm } from "./provider-signup-form";

import { Card, CardContent } from "@/components/ui/card";

/**
 * Powrót z Google/Facebook (#355).
 *
 * Błąd od dostawcy ma pierwszeństwo, bo przy anulowaniu sesja i tak wygląda na
 * oczekującą. Bez błędu o dalszym kroku decyduje stan sesji allauth.
 */
export function ProviderCallback() {
  const t = useTranslations();
  const locale = useLocale();
  const router = useRouter();
  const searchParams = useSearchParams();
  const { state, isChecking } = useSession();
  const error = searchParams.get("error");
  const isAuthenticated = state.status === "authenticated";

  useEffect(() => {
    if (!error && isAuthenticated) {
      router.replace(`/${locale}` as Route);
    }
  }, [error, isAuthenticated, locale, router]);

  if (error) {
    return <CallbackMessage message={t(providerErrorKey(error))} />;
  }

  if (isChecking || isAuthenticated) {
    return null;
  }

  if (state.status === "provider_signup_required") {
    return <ProviderSignupForm />;
  }

  return <CallbackMessage message={t("auth.provider.errors.failed")} />;
}

function CallbackMessage({ message }: { message: string }) {
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
