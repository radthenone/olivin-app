"use client";

import Link from "next/link";
import type { Route } from "next";
import { useLocale, useTranslations } from "next-intl";

import { useLogout, useSession } from "@olivin/features/auth";

import { Button } from "@/components/ui/button";

/**
 * Nagłówek pokazujący, na jakim koncie jest zalogowany klient.
 *
 * Sesja pochodzi z tego samego hooka `useSession` co reszta aplikacji, więc
 * login i logout odświeżają nagłówek przez unieważnienie klucza Orvala.
 */
export function SiteHeader() {
  const t = useTranslations("auth.header");
  const locale = useLocale();
  const { user, isChecking } = useSession();
  const { logout, isPending } = useLogout();

  return (
    <header className="border-b border-neutral-200 bg-neutral-0">
      <div className="mx-auto flex w-full max-w-2xl items-center justify-between gap-4 px-6 py-4">
        <Link
          className="text-lg font-semibold text-brand-600"
          href={`/${locale}` as Route}
        >
          Olivin
        </Link>

        <nav className="flex items-center gap-4 text-sm text-neutral-700">
          {!isChecking &&
            (user ? (
              <>
                <span>{t("signedInAs", { name: user.display })}</span>
                <Button
                  disabled={isPending}
                  onClick={() => {
                    void logout();
                  }}
                  size="sm"
                  type="button"
                  variant="outline"
                >
                  {isPending ? t("loggingOut") : t("logout")}
                </Button>
              </>
            ) : (
              <Link
                className="underline underline-offset-4"
                href={`/${locale}/login` as Route}
              >
                {t("login")}
              </Link>
            ))}
        </nav>
      </div>
    </header>
  );
}
