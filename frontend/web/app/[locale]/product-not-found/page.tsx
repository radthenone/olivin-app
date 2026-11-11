import { notFound } from "next/navigation";

/**
 * Cel rewrite'u z `proxy.ts` dla sluga, którego katalog nie zna.
 *
 * Strona wywołuje `notFound()` już w prerenderze, więc zostaje statyczna
 * i zawsze odpowiada prawdziwym 404 z tekstami 404 karty produktu. Własnego
 * adresu nie potrzebuje. Klient widzi swój pierwotny adres karty.
 */
export default function ProductNotFoundPage() {
  notFound();
}
