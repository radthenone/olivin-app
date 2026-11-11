"use client";

import Link from "next/link";
import type { Route } from "next";
import { useLocale, useTranslations } from "next-intl";

import { useLogout, useSession } from "@olivin/features/auth";

import { Button } from "@/components/ui/button";

/**
 * Nagłówek pokazujący, na jakim koncie jest zalogowany klient oraz nawigację.
 *
 * Sesja pochodzi z tego samego hooka `useSession` co reszta aplikacji, więc
 * login i logout odświeżają nagłówek przez unieważnienie klucza Orvala.
 */
export function SiteHeader() {
  const t = useTranslations("auth.header");
  const tCatalog = useTranslations("catalog.list");
  const locale = useLocale();
  const { user, isChecking } = useSession();
  const { logout, isPending } = useLogout();

  return (
    <header className="border-b border-neutral-200 bg-neutral-0">
      <div className="mx-auto flex w-full max-w-7xl items-center justify-between gap-4 px-6 py-4">
        <div className="flex items-center gap-6">
          <Link
            className="text-lg font-semibold text-brand-600"
            href={`/${locale}` as Route}
          >
            Olivin
          </Link>
          <Link
            className="text-sm font-medium text-neutral-700 transition-colors hover:text-brand-600"
            href={`/${locale}/products` as Route}
          >
            {tCatalog("title")}
          </Link>
        </div>

        <nav className="flex items-center gap-4 text-sm text-neutral-700">
          {!isChecking &&
            (user ? (
              <>
                <span>{t("signedInAs", { name: user.display })}</span>
                <Button
                  disabled={isPending}
                  onClick={() => {
                    // Nieudane wylogowanie nie może wywrócić aplikacji;
                    // użytkownik zostaje na koncie i może spróbować ponownie.
                    void logout().catch(() => undefined);
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
