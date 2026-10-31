"use client";

import type { Route } from "next";
import { useLocale, useTranslations } from "next-intl";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { useSession } from "@olivin/features/auth";

import { MfaForm } from "./mfa-form";
import { providerCallbackStep } from "./provider-callback-step";
import { ProviderCallbackMessage } from "./provider-callback-message";
import { providerErrorKey } from "./provider-error-key";
import { ProviderSignupForm } from "./provider-signup-form";

/**
 * Powrót z Google/Facebook (#355).
 *
 * Krok wybiera `providerCallbackStep`; tu tylko renderujemy go albo
 * przekierowujemy. MFA i weryfikacja e-maila działają jak przy logowaniu
 * hasłem i rejestracji e-mailem.
 */
export function ProviderCallback() {
  const t = useTranslations();
  const locale = useLocale();
  const router = useRouter();
  const searchParams = useSearchParams();
  const { state, isChecking } = useSession();
  const [isMfaExpired, setIsMfaExpired] = useState(false);
  const step = providerCallbackStep({
    error: searchParams.get("error"),
    isChecking,
    status: state.status,
  });

  useEffect(() => {
    if (step === "home") {
      router.replace(`/${locale}` as Route);
    }

    if (step === "verify_email") {
      router.replace(`/${locale}/register/verify` as Route);
    }
  }, [step, locale, router]);

  switch (step) {
    case "error":
      return (
        <ProviderCallbackMessage
          message={t(providerErrorKey(searchParams.get("error")))}
        />
      );
    case "mfa":
      if (isMfaExpired) {
        return (
          <ProviderCallbackMessage message={t("auth.errors.mfaExpired")} />
        );
      }

      return <MfaForm onExpired={() => setIsMfaExpired(true)} />;
    case "signup":
      return <ProviderSignupForm />;
    case "failed":
      return (
        <ProviderCallbackMessage message={t("auth.provider.errors.failed")} />
      );
    default:
      return null;
  }
}
