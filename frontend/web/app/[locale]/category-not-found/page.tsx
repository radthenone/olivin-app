import { notFound } from "next/navigation";

/**
 * Cel rewrite'u z `proxy.ts` dla sluga kategorii, której katalog nie zna.
 */
export default function CategoryNotFoundPage() {
  notFound();
}
