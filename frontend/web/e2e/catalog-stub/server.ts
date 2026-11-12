import {
  createServer,
  type IncomingMessage,
  type ServerResponse,
} from "node:http";

import type {
  Category,
  Collection,
  PaginatedProductListList,
  ProductDetail,
  ProductList,
  ProductVariant,
} from "@olivin/api/generated/apps/schemas";
import { isCatalogSlug } from "../../src/lib/catalog-url";

/**
 * Stub API katalogu dla testów przeglądarkowych (#357, #359, #360).
 *
 * Odpowiedzi są typowane schematami Orvala. Stub symuluje endpointy katalogu:
 * kartę produktu, listę opublikowanych produktów ze stronicowaniem, drzewo
 * kategorii, kolekcje oraz filtry i wyszukiwanie.
 */

const port = Number(process.env.E2E_STUB_PORT) || 3200;
/** Kurs zastępczy: backend przelicza po kursie NBP, stub tylko symuluje kierunek. */
const PLN_PER_EUR = 4.3;

export type Language = "pl" | "en";
export type Currency = "PLN" | "EUR";

export type Fixture = {
  product: ProductDetail;
  name: Record<Language, string>;
  description: Record<Language, string>;
  collections?: string[];
};

export type CategoryFixture = {
  id: string;
  slug: string;
  name: Record<Language, string>;
  children?: CategoryFixture[];
};

export type CollectionFixture = {
  id: string;
  slug: string;
  name: Record<Language, string>;
  description: Record<Language, string>;
};

function variant(
  overrides: Partial<ProductVariant> &
    Pick<
      ProductVariant,
      "sku" | "metalColor" | "price" | "isAvailable" | "isLowStock"
    >,
): ProductVariant {
  return {
    id: overrides.sku,
    available: overrides.isAvailable ? 10 : 0,
    size: "17",
    length: "45",
    stone: "diamond",
    metalWeightGrams: "4.200",
    vatRate: "0.2300",
    isVatExempt: false,
    vatExemptionBasis: "",
    images: [],
    gemstones: [],
    ...overrides,
  };
}

function ring(): Fixture {
  return {
    product: {
      id: "11111111-1111-1111-1111-111111111111",
      name: "Złoty pierścionek",
      slug: "ring",
      description: "Pierścionek z żółtego złota z diamentem.",
      category: "pierscionki",
      material: "gold",
      fineness: "585",
      isMadeToOrder: false,
      productionTimeDays: null,
      isEngravable: true,
      engravingPrice: { amount: 5000, currency: "PLN" },
      images: [
        {
          id: "image-ring",
          position: 1,
          isPrimary: true,
          altText: "Złoty pierścionek z diamentem na białym tle",
          urls: {
            "400": "/images/ring.svg",
            "800": "/images/ring.svg",
            "1600": "/images/ring.svg",
          },
        },
      ],
      variants: [
        variant({
          sku: "RING-Y-17",
          metalColor: "yellow",
          size: "17",
          price: { amount: 250_000, currency: "PLN" },
          isAvailable: true,
          isLowStock: false,
          images: [
            {
              id: "image-ring",
              position: 1,
              isPrimary: true,
              altText: "Złoty pierścionek z diamentem na białym tle",
              urls: {
                "400": "/images/ring.svg",
                "800": "/images/ring.svg",
                "1600": "/images/ring.svg",
              },
            },
          ],
        }),
        variant({
          sku: "RING-Y-16",
          metalColor: "yellow",
          size: "16",
          price: { amount: 245_000, currency: "PLN" },
          isAvailable: true,
          isLowStock: false,
          images: [
            {
              id: "image-ring",
              position: 1,
              isPrimary: true,
              altText: "Złoty pierścionek z diamentem na białym tle",
              urls: {
                "400": "/images/ring.svg",
                "800": "/images/ring.svg",
                "1600": "/images/ring.svg",
              },
            },
          ],
        }),
        variant({
          sku: "RING-W-17",
          metalColor: "white",
          size: "17",
          price: { amount: 260_000, currency: "PLN" },
          isAvailable: true,
          isLowStock: true,
          available: 2,
          images: [
            {
              id: "image-ring-white",
              position: 1,
              isPrimary: true,
              altText: "Biały pierścionek z diamentem na białym tle",
              urls: {
                "400": "/images/ring-white.svg",
                "800": "/images/ring-white.svg",
                "1600": "/images/ring-white.svg",
              },
            },
          ],
        }),
        variant({
          sku: "RING-R-17",
          metalColor: "rose",
          size: "17",
          price: { amount: 270_000, currency: "PLN" },
          isAvailable: false,
          isLowStock: false,
          available: 0,
        }),
      ],
      averageRating: 4.5,
      isFavorite: false,
    },
    name: { pl: "Złoty pierścionek", en: "Gold ring" },
    description: {
      pl: "Pierścionek z żółtego złota z diamentem.",
      en: "A yellow gold ring set with a diamond.",
    },
    collections: ["lato-2026"],
  };
}

function necklace(): Fixture {
  return {
    product: {
      id: "22222222-2222-2222-2222-222222222222",
      name: "Naszyjnik na zamówienie",
      slug: "necklace",
      description: "Naszyjnik wykonywany na zamówienie.",
      category: "naszyjniki",
      material: "silver",
      fineness: "925",
      isMadeToOrder: true,
      productionTimeDays: 14,
      isEngravable: false,
      engravingPrice: null,
      images: [
        {
          id: "image-necklace",
          position: 1,
          isPrimary: true,
          altText: "Srebrny naszyjnik na białym tle",
          urls: {
            "400": "/images/necklace.svg",
            "800": "/images/necklace.svg",
            "1600": "/images/necklace.svg",
          },
        },
      ],
      variants: [
        variant({
          sku: "NECKLACE-S-45",
          metalColor: "white",
          size: "17",
          length: "45",
          price: { amount: 189_000, currency: "PLN" },
          available: null,
          isAvailable: true,
          isLowStock: false,
          images: [
            {
              id: "image-necklace",
              position: 1,
              isPrimary: true,
              altText: "Srebrny naszyjnik na białym tle",
              urls: {
                "400": "/images/necklace.svg",
                "800": "/images/necklace.svg",
                "1600": "/images/necklace.svg",
              },
            },
          ],
        }),
      ],
      averageRating: null,
      isFavorite: false,
    },
    name: { pl: "Naszyjnik na zamówienie", en: "Made-to-order necklace" },
    description: {
      pl: "Naszyjnik wykonywany na zamówienie.",
      en: "A necklace made to order.",
    },
  };
}

function makeProduct(
  slug: string,
  plName: string,
  enName: string,
  category: string,
  priceAmount: number,
  collections: string[] = [],
  materialOverride?: "gold" | "silver" | "platinum" | "palladium",
): Fixture {
  const material =
    materialOverride ?? (slug.includes("silver") ? "silver" : "gold");
  return {
    product: {
      id: `id-${slug}`,
      name: plName,
      slug,
      description: `Opis ${plName}.`,
      category,
      material,
      fineness: material === "silver" ? "925" : "585",
      isMadeToOrder: false,
      productionTimeDays: null,
      isEngravable: false,
      engravingPrice: null,
      images: [
        {
          id: `image-${slug}`,
          position: 1,
          isPrimary: true,
          altText: plName,
          urls: {
            "400": `/images/${slug}.svg`,
            "800": `/images/${slug}.svg`,
            "1600": `/images/${slug}.svg`,
          },
        },
      ],
      variants: [
        variant({
          sku: `SKU-${slug.toUpperCase()}`,
          metalColor: "yellow",
          price: { amount: priceAmount, currency: "PLN" },
          isAvailable: true,
          isLowStock: false,
          images: [
            {
              id: `image-${slug}`,
              position: 1,
              isPrimary: true,
              altText: plName,
              urls: {
                "400": `/images/${slug}.svg`,
                "800": `/images/${slug}.svg`,
                "1600": `/images/${slug}.svg`,
              },
            },
          ],
        }),
      ],
      averageRating: 5.0,
      isFavorite: false,
    },
    name: { pl: plName, en: enName },
    description: {
      pl: `Opis dla ${plName}.`,
      en: `Description for ${enName}.`,
    },
    collections,
  };
}

export function initialFixtures(): Record<string, Fixture> {
  const result: Record<string, Fixture> = {
    ring: ring(),
    necklace: necklace(),
    "earrings-gold": makeProduct(
      "earrings-gold",
      "Złote kolczyki",
      "Gold earrings",
      "kolczyki",
      120_000,
      ["lato-2026"],
      "gold",
    ),
    "earrings-silver": makeProduct(
      "earrings-silver",
      "Srebrne kolczyki",
      "Silver earrings",
      "kolczyki",
      85_000,
      [],
      "silver",
    ),
    "ring-sapphire": makeProduct(
      "ring-sapphire",
      "Pierścionek z szafirem",
      "Sapphire ring",
      "zareczynowe",
      310_000,
      ["lato-2026"],
    ),
    "ring-ruby": makeProduct(
      "ring-ruby",
      "Pierścionek z rubinem",
      "Ruby ring",
      "zareczynowe",
      340_000,
    ),
  };

  // Dodajemy dodatkowe produkty 1..10, aby łączna liczba wynosiła 16 (dwie strony przy pageSize 12)
  for (let i = 1; i <= 10; i++) {
    const slug = `product-extra-${i}`;
    result[slug] = makeProduct(
      slug,
      `Produkt dodatkowy ${i}`,
      `Extra product ${i}`,
      "pierscionki",
      100_000 + i * 10_000,
    );
  }

  return result;
}

let fixtures: Record<string, Fixture> = initialFixtures();

export const categoryTreeFixtures: CategoryFixture[] = [
  {
    id: "cat-pierscionki",
    slug: "pierscionki",
    name: { pl: "Pierścionki", en: "Rings" },
    children: [
      {
        id: "cat-zareczynowe",
        slug: "zareczynowe",
        name: { pl: "Pierścionki zaręczynowe", en: "Engagement rings" },
      },
    ],
  },
  {
    id: "cat-naszyjniki",
    slug: "naszyjniki",
    name: { pl: "Naszyjniki", en: "Necklaces" },
  },
  {
    id: "cat-kolczyki",
    slug: "kolczyki",
    name: { pl: "Kolczyki", en: "Earrings" },
  },
];

export const collectionFixtures: CollectionFixture[] = [
  {
    id: "col-lato-2026",
    slug: "lato-2026",
    name: { pl: "Kolekcja Letnia 2026", en: "Summer Collection 2026" },
    description: {
      pl: "Biżuteria na słoneczne dni.",
      en: "Jewelry for sunny days.",
    },
  },
];

function findCategoryFixture(
  slug: string,
  tree: CategoryFixture[] = categoryTreeFixtures,
): CategoryFixture | null {
  for (const item of tree) {
    if (item.slug === slug) {
      return item;
    }
    if (item.children) {
      const found = findCategoryFixture(slug, item.children);
      if (found) {
        return found;
      }
    }
  }
  return null;
}

function getSubtreeCategorySlugs(cat: CategoryFixture): string[] {
  const slugs = [cat.slug];
  if (cat.children) {
    for (const child of cat.children) {
      slugs.push(...getSubtreeCategorySlugs(child));
    }
  }
  return slugs;
}

function mapCategory(cat: CategoryFixture, lang: Language): Category {
  return {
    id: cat.id,
    name: cat.name[lang],
    slug: cat.slug,
    children: cat.children ? cat.children.map((c) => mapCategory(c, lang)) : [],
  };
}

/**
 * Przelicza kwotę na walutę odpowiedzi.
 */
function convert(amount: number, currency: Currency): number {
  if (currency === "PLN") {
    return amount;
  }

  const cents = amount / PLN_PER_EUR;
  return Math.ceil(cents / 50) * 50;
}

function localise(
  product: ProductDetail,
  fixture: Fixture,
  language: Language,
  currency: Currency,
  origin: string,
): ProductDetail {
  return {
    ...product,
    name: fixture.name[language],
    description: fixture.description[language],
    engravingPrice: product.engravingPrice
      ? {
          amount: convert(product.engravingPrice.amount, currency),
          currency,
        }
      : null,
    images: product.images.map((image) => ({
      ...image,
      urls: Object.fromEntries(
        Object.entries(image.urls).map(([width, path]) => [
          width,
          `${origin}${path}`,
        ]),
      ),
    })),
    variants: product.variants.map((item) => ({
      ...item,
      images: item.images.map((image) => ({
        ...image,
        urls: Object.fromEntries(
          Object.entries(image.urls).map(([width, path]) => [
            width,
            `${origin}${path}`,
          ]),
        ),
      })),
      price: { amount: convert(item.price.amount, currency), currency },
    })),
  };
}

function toProductList(
  product: ProductDetail,
  fixture: Fixture,
  language: Language,
  currency: Currency,
  origin: string,
): ProductList {
  const localisedDetail = localise(
    product,
    fixture,
    language,
    currency,
    origin,
  );
  // Backend zwraca najtańszy wariant, nie pierwszy z listy.
  const cheapest =
    [...localisedDetail.variants].sort(
      (a, b) => a.price.amount - b.price.amount,
    )[0] ?? null;

  return {
    id: localisedDetail.id,
    name: localisedDetail.name,
    slug: localisedDetail.slug,
    category: localisedDetail.category,
    material: localisedDetail.material,
    fineness: localisedDetail.fineness,
    isMadeToOrder: localisedDetail.isMadeToOrder,
    productionTimeDays: localisedDetail.productionTimeDays,
    isEngravable: localisedDetail.isEngravable,
    engravingPrice: localisedDetail.engravingPrice,
    cheapestVariant: cheapest,
    averageRating: localisedDetail.averageRating,
    isFavorite: localisedDetail.isFavorite,
  };
}

function json(response: ServerResponse, status: number, body: unknown): void {
  response.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "access-control-allow-origin": "*",
  });
  response.end(JSON.stringify(body));
}

function svg(response: ServerResponse): void {
  response.writeHead(200, { "content-type": "image/svg+xml" });
  response.end(
    '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="800"><rect width="800" height="800" fill="#e8e2d8"/></svg>',
  );
}

async function readBody(request: IncomingMessage): Promise<unknown> {
  const chunks: Buffer[] = [];

  for await (const chunk of request) {
    chunks.push(chunk as Buffer);
  }

  const text = Buffer.concat(chunks).toString("utf8");
  return text.length > 0 ? JSON.parse(text) : undefined;
}

function originOf(request: IncomingMessage): string {
  return `http://${request.headers.host ?? `localhost:${port}`}`;
}

/**
 * Zwraca nazwę pierwszego parametru z niepoprawną wartością filtra.
 *
 * Backend odpowiada 400 na niepoprawne filtry: cena nie jest skończoną liczbą
 * albo któryś parametr zawiera NUL (Postgres go odrzuca).
 *
 * Args:
 *     searchParams: Parametry zapytania URL.
 *
 * Returns:
 *     Nazwa parametru albo `null`, gdy wszystkie wartości są poprawne.
 */
export function findInvalidFilterParam(
  searchParams: URLSearchParams,
): string | null {
  for (const key of ["priceMin", "priceMax"]) {
    const value = searchParams.get(key)?.trim();
    if (value && !Number.isFinite(Number(value))) {
      return key;
    }
  }
  for (const [key, value] of searchParams) {
    if (value.includes("\u0000")) {
      return key;
    }
  }
  return null;
}

/**
 * Filtruje i sortuje fixtures wg parametrów zapytania URL.
 */
export function filterAndSortFixtures(
  fixturesList: Fixture[],
  searchParams: URLSearchParams,
  language: Language,
): Fixture[] {
  let list = [...fixturesList];

  const categoryParam = searchParams.get("category");
  if (categoryParam) {
    if (!isCatalogSlug(categoryParam)) {
      return [];
    }
    const catFixture = findCategoryFixture(categoryParam);
    const allowedCategories = catFixture
      ? getSubtreeCategorySlugs(catFixture)
      : [categoryParam];
    list = list.filter((f) => allowedCategories.includes(f.product.category));
  }

  const collectionParam = searchParams.get("collection");
  if (collectionParam) {
    if (!isCatalogSlug(collectionParam)) {
      return [];
    }
    list = list.filter((f) => f.collections?.includes(collectionParam));
  }

  const search = searchParams.get("search")?.toLowerCase().trim();
  if (search) {
    list = list.filter((f) => {
      const namePl = f.name.pl.toLowerCase();
      const nameEn = f.name.en.toLowerCase();
      const descPl = f.description.pl.toLowerCase();
      const descEn = f.description.en.toLowerCase();
      return (
        namePl.includes(search) ||
        nameEn.includes(search) ||
        descPl.includes(search) ||
        descEn.includes(search)
      );
    });
  }

  const material = searchParams.get("material");
  if (material) {
    list = list.filter((f) => f.product.material === material);
  }

  const fineness = searchParams.get("fineness");
  if (fineness) {
    list = list.filter((f) => f.product.fineness === fineness);
  }

  const metalColor = searchParams.get("metalColor");
  if (metalColor) {
    list = list.filter((f) =>
      f.product.variants.some((v) => v.metalColor === metalColor),
    );
  }

  const stone = searchParams.get("stone");
  if (stone) {
    list = list.filter((f) =>
      f.product.variants.some((v) => v.stone === stone),
    );
  }

  const size = searchParams.get("size");
  if (size) {
    list = list.filter((f) => f.product.variants.some((v) => v.size === size));
  }

  const length = searchParams.get("length");
  if (length) {
    list = list.filter((f) =>
      f.product.variants.some((v) => v.length === length),
    );
  }

  const getCheapestPrice = (f: Fixture): number => {
    return Math.min(...f.product.variants.map((v) => v.price.amount));
  };

  const priceMin = Number(searchParams.get("priceMin"));
  if (!Number.isNaN(priceMin) && priceMin > 0) {
    list = list.filter((f) => getCheapestPrice(f) >= priceMin);
  }

  const priceMax = Number(searchParams.get("priceMax"));
  if (!Number.isNaN(priceMax) && priceMax > 0) {
    list = list.filter((f) => getCheapestPrice(f) <= priceMax);
  }

  const ordering = searchParams.get("ordering") ?? "newest";
  if (ordering === "price") {
    list.sort((a, b) => getCheapestPrice(a) - getCheapestPrice(b));
  } else if (ordering === "-price") {
    list.sort((a, b) => getCheapestPrice(b) - getCheapestPrice(a));
  } else if (ordering === "name") {
    list.sort((a, b) =>
      a.name[language].localeCompare(b.name[language], language),
    );
  } else if (ordering === "-name") {
    list.sort((a, b) =>
      b.name[language].localeCompare(a.name[language], language),
    );
  }

  return list;
}

export const server = createServer(async (request, response) => {
  const url = new URL(request.url ?? "/", originOf(request));
  const origin = originOf(request);
  const language: Language =
    url.searchParams.get("lang") === "en" ? "en" : "pl";
  const currency: Currency =
    url.searchParams.get("currency") === "EUR" ? "EUR" : "PLN";

  if (request.method === "GET" && url.pathname === "/health/") {
    json(response, 200, { status: "ok" });
    return;
  }

  if (request.method === "GET" && url.pathname.startsWith("/images/")) {
    svg(response);
    return;
  }

  if (request.method === "POST" && url.pathname === "/__test__/fixture") {
    const body = (await readBody(request)) as {
      slug?: string;
      priceAmount?: number;
      name?: string;
    };

    if (
      !body?.slug ||
      (typeof body.priceAmount !== "number" && typeof body.name !== "string")
    ) {
      json(response, 400, {
        detail: "Wymagane slug oraz priceAmount lub name.",
      });
      return;
    }

    const fixture = fixtures[body.slug];
    if (!fixture) {
      json(response, 404, { detail: "Nieznany fixture." });
      return;
    }

    fixtures = {
      ...fixtures,
      [body.slug]: {
        ...fixture,
        name:
          typeof body.name === "string"
            ? { ...fixture.name, pl: body.name }
            : fixture.name,
        product: {
          ...fixture.product,
          variants:
            typeof body.priceAmount === "number"
              ? fixture.product.variants.map((item) => ({
                  ...item,
                  price: {
                    amount: body.priceAmount as number,
                    currency: "PLN" as const,
                  },
                }))
              : fixture.product.variants,
        },
      },
    };
    json(response, 200, { status: "ok" });
    return;
  }

  if (request.method === "DELETE" && url.pathname === "/__test__/fixture") {
    fixtures = initialFixtures();
    json(response, 200, { status: "ok" });
    return;
  }

  // GET /categories/
  if (request.method === "GET" && url.pathname === "/categories/") {
    const tree: Category[] = categoryTreeFixtures.map((cat) =>
      mapCategory(cat, language),
    );
    json(response, 200, tree);
    return;
  }

  // GET /categories/{slug}/
  const categoryMatch = /^\/categories\/([^/]+)\/$/.exec(url.pathname);
  if (request.method === "GET" && categoryMatch) {
    const slug = categoryMatch[1];
    if (!isCatalogSlug(slug)) {
      json(response, 404, { detail: "Niepoprawny slug." });
      return;
    }

    const found = findCategoryFixture(slug);
    if (!found) {
      json(response, 404, { detail: "Nie znaleziono kategorii." });
      return;
    }

    json(response, 200, mapCategory(found, language));
    return;
  }

  // GET /collections/
  if (request.method === "GET" && url.pathname === "/collections/") {
    const items: Collection[] = collectionFixtures.map((col) => {
      const count = Object.values(fixtures).filter((f) =>
        f.collections?.includes(col.slug),
      ).length;
      return {
        id: col.id,
        name: col.name[language],
        slug: col.slug,
        description: col.description[language],
        productCount: count,
      };
    });
    json(response, 200, { count: items.length, results: items });
    return;
  }

  // GET /collections/{slug}/
  const collectionMatch = /^\/collections\/([^/]+)\/$/.exec(url.pathname);
  if (request.method === "GET" && collectionMatch) {
    const slug = collectionMatch[1];
    if (!isCatalogSlug(slug)) {
      json(response, 404, { detail: "Niepoprawny slug." });
      return;
    }

    const found = collectionFixtures.find((c) => c.slug === slug);
    if (!found) {
      json(response, 404, { detail: "Nie znaleziono kolekcji." });
      return;
    }

    const count = Object.values(fixtures).filter((f) =>
      f.collections?.includes(found.slug),
    ).length;
    const col: Collection = {
      id: found.id,
      name: found.name[language],
      slug: found.slug,
      description: found.description[language],
      productCount: count,
    };
    json(response, 200, col);
    return;
  }

  // GET /products/
  if (request.method === "GET" && url.pathname === "/products/") {
    const page = Math.max(1, Number(url.searchParams.get("page")) || 1);
    const pageSize = Math.max(
      1,
      Number(url.searchParams.get("pageSize")) || 12,
    );

    const invalidParam = findInvalidFilterParam(url.searchParams);
    if (invalidParam) {
      json(response, 400, { [invalidParam]: ["Niepoprawna wartość filtra."] });
      return;
    }

    const list = filterAndSortFixtures(
      Object.values(fixtures),
      url.searchParams,
      language,
    );

    const totalCount = list.length;
    const startIndex = (page - 1) * pageSize;
    const paged = list.slice(startIndex, startIndex + pageSize);

    const results: ProductList[] = paged.map((f) =>
      toProductList(f.product, f, language, currency, origin),
    );

    const payload: PaginatedProductListList = {
      count: totalCount,
      next:
        startIndex + pageSize < totalCount
          ? `${origin}/products/?page=${page + 1}`
          : null,
      previous: page > 1 ? `${origin}/products/?page=${page - 1}` : null,
      results,
    };

    json(response, 200, payload);
    return;
  }

  // GET /products/{slug}/
  const productMatch = /^\/products\/([^/]+)\/$/.exec(url.pathname);
  if (request.method === "GET" && productMatch) {
    const slug = productMatch[1];
    if (!isCatalogSlug(slug)) {
      json(response, 404, { detail: "Niepoprawny slug." });
      return;
    }

    const fixture = fixtures[slug];
    if (!fixture) {
      json(response, 404, { detail: "Nie znaleziono." });
      return;
    }

    json(
      response,
      200,
      localise(fixture.product, fixture, language, currency, origin),
    );
    return;
  }

  json(response, 404, { detail: "Nie znaleziono." });
});

// Uruchamiamy listen tylko gdy skrypt jest bezpośrednim punktem wejścia
const isDirectRun =
  // Separatory z Windows (Git Bash) też muszą pasować do ścieżki.
  process.argv[1]?.replace(/\\/g, "/").endsWith("catalog-stub/server.ts") ||
  process.env.RUN_CATALOG_STUB === "1";

if (isDirectRun) {
  server.listen(port, () => {
    console.log(`Stub API katalogu nasłuchuje na http://localhost:${port}`);
  });
}
