"use client";

import { useTranslations } from "next-intl";

/**
 * 404 strony kategorii. Renderuje się pod prefiksem języka.
 */
export default function CategoryNotFound() {
  const t = useTranslations("catalog.category.notFound");

  return (
    <main className="mx-auto w-full max-w-3xl px-6 py-16">
      <h1 className="text-3xl font-semibold text-brand-600">{t("title")}</h1>
      <p className="mt-4 text-base text-neutral-700">{t("description")}</p>
    </main>
  );
}
