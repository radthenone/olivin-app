"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import {
  DELIVERY_COUNTRY_COOKIE_NAME,
  EU_DELIVERY_COUNTRIES,
  isEuDeliveryCountry,
  type DeliveryCountry,
} from "@olivin/features/catalog";

import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";

/**
 * Zapisuje kraj dostawy w cookie na rok (ADR 0035); `Secure` tylko po HTTPS.
 *
 * Args:
 *     country: Kraj dostawy wybrany przez klienta.
 */
function saveDeliveryCountryCookie(country: DeliveryCountry) {
  const secure = location.protocol === "https:" ? "; Secure" : "";
  document.cookie = `${DELIVERY_COUNTRY_COOKIE_NAME}=${country}; path=/; max-age=31536000; SameSite=Lax${secure}`;
}

/**
 * Przełącznik kraju dostawy w nagłówku strony (ADR 0035).
 *
 * Prezentuje listę wyłącznie 27 państw członkowskich Unii Europejskiej.
 * Wybór zapisuje się w ciasteczku `delivery_country` i natychmiast odświeża
 * komponenty serwerowe (router.refresh). Waluta wynika wyłącznie z kraju.
 *
 * Początkowy kraj przychodzi z serwera (cookie `delivery_country` czytane
 * w `DeliveryCountrySwitchLoader`), więc stan nie wymaga efektu i po
 * przeładowaniu nie ma mignięcia domyślnego kraju.
 */
export function DeliveryCountrySwitch({
  initialCountry,
}: {
  initialCountry: DeliveryCountry;
}) {
  const t = useTranslations("delivery");
  const router = useRouter();
  const [country, setCountry] = React.useState<DeliveryCountry>(initialCountry);

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    if (!isEuDeliveryCountry(value)) {
      return;
    }

    setCountry(value);
    saveDeliveryCountryCookie(value);
    router.refresh();
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
        className="h-8 w-auto min-w-28 border-neutral-300 bg-neutral-0 py-0 pl-2 pr-6 text-xs text-neutral-800"
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
