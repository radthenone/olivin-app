"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import {
  DELIVERY_COUNTRY_COOKIE_NAME,
  EU_DELIVERY_COUNTRIES,
  currencyFromDeliveryCountry,
  isEuDeliveryCountry,
  type DeliveryCountry,
} from "@olivin/features/catalog";
import { useSession } from "@olivin/features/auth";
import {
  customersProfileList,
  customersProfilePartialUpdate,
} from "@olivin/api/generated/apps/profiles/profiles";

import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";

function getClientCookieCountry(): DeliveryCountry {
  if (typeof document === "undefined") return "PL";
  const match = document.cookie.match(
    new RegExp(`(?:^|; )${DELIVERY_COUNTRY_COOKIE_NAME}=([^;]*)`),
  );
  if (match && isEuDeliveryCountry(match[1])) {
    return match[1];
  }
  return "PL";
}

/**
 * Przełącznik kraju dostawy w nagłówku strony (ADR 0035).
 *
 * Prezentuje listę wyłącznie 27 państw członkowskich Unii Europejskiej.
 * Wybór zapisuje się w ciasteczku (oraz w profilu zalogowanego użytkownika)
 * i natychmiast odświeża komponenty serwerowe (router.refresh).
 */
export function DeliveryCountrySwitch({
  initialCountry,
}: {
  initialCountry?: DeliveryCountry;
}) {
  const t = useTranslations("delivery");
  let router: ReturnType<typeof useRouter> | null = null;
  try {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    router = useRouter();
  } catch {
    // Brak routera w środowisku testowym
  }

  let isAuthenticated = false;
  try {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    const session = useSession();
    isAuthenticated = session.isAuthenticated;
  } catch {
    // Brak QueryClientProvider
  }

  const [country, setCountry] = React.useState<DeliveryCountry>(
    initialCountry ?? "PL",
  );

  React.useEffect(() => {
    if (!initialCountry) {
      setCountry(getClientCookieCountry());
    }
  }, [initialCountry]);

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    if (!isEuDeliveryCountry(value)) {
      return;
    }

    setCountry(value);
    const currency = currencyFromDeliveryCountry(value);

    // Zapisujemy kraj dostawy i walutę w cookie (ADR 0035)
    document.cookie = `${DELIVERY_COUNTRY_COOKIE_NAME}=${value}; path=/; max-age=31536000; SameSite=Lax`;
    document.cookie = `currency=${currency}; path=/; max-age=31536000; SameSite=Lax`;

    // U zalogowanego klienta zapisujemy kraj również w profilu (ADR 0035)
    if (isAuthenticated) {
      void (async () => {
        try {
          const listRes = await customersProfileList();
          const profile = listRes.data.results?.[0];
          if (profile?.id) {
            await customersProfilePartialUpdate(profile.id, {
              deliveryCountry: value,
            });
          }
        } catch {
          // Błąd zapisu profilu nie cofa wyboru w cookie
        }
      })();
    }

    router?.refresh();
  };

  return (
    <div className="flex items-center gap-2">
      <Label
        className="text-xs text-neutral-600 whitespace-nowrap"
        htmlFor="delivery-country-select"
      >
        {t("shipTo")}
      </Label>
      <Select
        aria-label={t("shipTo")}
        className="h-8 w-auto min-w-[7rem] border-neutral-300 bg-neutral-0 py-0 pl-2 pr-6 text-xs text-neutral-800"
        id="delivery-country-select"
        name="deliveryCountry"
        onChange={handleChange}
        value={country}
      >
        {EU_DELIVERY_COUNTRIES.map((c) => (
          <option key={c} value={c}>
            {t(`countries.${c}`)}
          </option>
        ))}
      </Select>
    </div>
  );
}
