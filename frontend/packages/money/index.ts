// Formatowanie i prezentacja kwot po stronie klienta.
//
// Zakres: wyłącznie prezentacja — formatowanie liczby całkowitej groszy na
// napis w walucie, zgodnie z lokalizacją. Arytmetyka pieniędzy nie należy
// tutaj. Kwota do zapłaty, podatek i podział rabatu na pozycje liczone są
// wyłącznie na backendzie, bo frontend nie może być źródłem prawdy o tym,
// ile klient płaci.
//
// Reprezentacja: liczba całkowita w najmniejszej jednostce waluty plus jawny
// kod waluty — patrz docs/adr/0009-kwoty-jako-liczby-calkowite.md

/** Kwota w najmniejszej jednostce waluty plus kod ISO 4217 (ADR 0009). */
export type Money = {
  amount: number;
  currency: string;
};

/**
 * Formatuje kwotę z API według języka i waluty.
 *
 * Args:
 *     money: Kwota w najmniejszej jednostce waluty i kod ISO 4217.
 *     locale: Język interfejsu (`pl` albo `en`), niezależny od waluty.
 *
 * Returns:
 *     Napis gotowy do pokazania klientowi, np. `1 234,50 zł`.
 */
export function formatMoney(money: Money, locale: string): string {
  // Dzielenie przez 100 zakłada dwa miejsca po przecinku (PLN, EUR, USD); waluty
  // o innej liczbie miejsc wymagałyby wykładnika per waluta.
  return new Intl.NumberFormat(locale, {
    style: "currency",
    currency: money.currency,
  }).format(money.amount / 100);
}
