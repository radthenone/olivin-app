"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useSession } from "@olivin/features/auth";
import {
  EU_DELIVERY_COUNTRIES,
  isEuDeliveryCountry,
  saveDeliveryCountryCookie,
  saveProfileDeliveryCountry,
  type DeliveryCountry,
} from "@olivin/features/catalog";

import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";

/**
 * Przełącznik kraju dostawy w nagłówku strony (ADR 0035, #363).
 *
 * Prezentuje listę wyłącznie 27 państw członkowskich Unii Europejskiej.
 * Wybór zapisuje się w ciasteczku `delivery_country` i natychmiast odświeża
 * komponenty serwerowe (router.refresh). Waluta wynika wyłącznie z kraju.
 *
 * U zalogowanego klienta zmiana zapisuje kraj również w profilu klienta.
 * W razie błędu zapisu profilu ciasteczko i wybór w select nie są cofane,
 * a użytkownik widzi komunikat błędu.
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
  const { isAuthenticated } = useSession();
  const [country, setCountry] = React.useState<DeliveryCountry>(initialCountry);
  const [error, setError] = React.useState<string | null>(null);
  const [syncedInitial, setSyncedInitial] =
    React.useState<DeliveryCountry>(initialCountry);

  // Kraj z serwera zmienia się bez remontażu (np. po zalogowaniu profil
  // nadpisuje cookie i router.refresh dostarcza nowy props). Stan z props
  // synchronizujemy w trakcie renderu, nie kasując komunikatu błędu.
  if (syncedInitial !== initialCountry) {
    setSyncedInitial(initialCountry);
    setCountry(initialCountry);
  }

  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    if (!isEuDeliveryCountry(value)) {
      return;
    }

    setCountry(value);
    saveDeliveryCountryCookie(value);
    setError(null);
    router.refresh();

    if (isAuthenticated) {
      void saveProfileDeliveryCountry(value).catch(() => {
        setError(t("saveError"));
      });
    }
  };

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center gap-2">
        <Label
          className="whitespace-nowrap text-xs text-neutral-600"
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
      {error && (
        <p className="text-xs text-destructive" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
