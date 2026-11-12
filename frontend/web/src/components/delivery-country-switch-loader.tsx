import { DeliveryCountrySwitch } from "@/components/delivery-country-switch";
import { getRequestDeliveryCountry } from "@/lib/catalog-api";

/**
 * Przełącznik kraju dostawy z krajem odczytanym z cookie po stronie serwera.
 *
 * Czytanie cookie czyni ten fragment dynamicznym (Cache Components), więc
 * trzeba go owinąć w `<Suspense>`. Brak cookie oznacza Polskę.
 */
export async function DeliveryCountrySwitchLoader() {
  const country = await getRequestDeliveryCountry();

  const initialCountry = country ?? "PL";

  // `key` remontuje przełącznik po zmianie kraju z serwera (np. po zalogowaniu,
  // gdy profil nadpisuje cookie), bo stan wewnątrz ignoruje nowy props.
  return (
    <DeliveryCountrySwitch
      key={initialCountry}
      initialCountry={initialCountry}
    />
  );
}
