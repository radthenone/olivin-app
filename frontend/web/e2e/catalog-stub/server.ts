import {
  createServer,
  type IncomingMessage,
  type ServerResponse,
} from "node:http";

import type {
  ProductDetail,
  ProductVariant,
} from "@olivin/api/generated/apps/schemas";

/**
 * Stub API katalogu dla testów przeglądarkowych (#357).
 *
 * Odpowiedzi są typowane schematami Orvala, więc rozjazd kontraktu wyłapuje
 * typecheck, a nie dopiero test. Stub udaje wyłącznie to, czego potrzebuje
 * plasterek katalogu: kartę produktu w dwóch językach i dwóch walutach.
 * Domyślnie działa na porcie 3200 i jest uruchamiany jako dodatkowy
 * `webServer` Playwrighta — CI nie potrzebuje Django.
 *
 * Punkt testowy `POST /__test__/fixture` podmienia dane (np. cenę), żeby test
 * mógł zasymulować zmianę po stronie backendu.
 */

const port = Number(process.env.E2E_STUB_PORT) || 3200;
/** Kurs zastępczy: backend przelicza po kursie NBP, stub tylko symuluje kierunek. */
const PLN_PER_EUR = 4.3;

type Language = "pl" | "en";
type Currency = "PLN" | "EUR";

type Fixture = {
  product: ProductDetail;
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
          price: { amount: 250_000, currency: "PLN" },
          isAvailable: true,
          isLowStock: false,
        }),
        variant({
          sku: "RING-W-17",
          metalColor: "white",
          price: { amount: 260_000, currency: "PLN" },
          isAvailable: true,
          isLowStock: true,
          available: 2,
        }),
        variant({
          sku: "RING-R-17",
          metalColor: "rose",
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

let fixtures: Record<string, Fixture> = {
  ring: ring(),
  necklace: necklace(),
};

/**
 * Przelicza kwotę na walutę odpowiedzi. Stub zaokrągla w górę do 50 groszy,
 * tak jak backend przy euro (ADR 0019) — test widzi zmianę waluty.
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
      price: { amount: convert(item.price.amount, currency), currency },
    })),
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

const server = createServer(async (request, response) => {
  const url = new URL(request.url ?? "/", originOf(request));
  const origin = originOf(request);

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
      currency?: Currency;
    };

    if (!body?.slug || typeof body.priceAmount !== "number") {
      json(response, 400, { detail: "Wymagane slug i priceAmount." });
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
        product: {
          ...fixture.product,
          variants: fixture.product.variants.map((item) => ({
            ...item,
            price: { amount: body.priceAmount as number, currency: "PLN" },
          })),
        },
      },
    };
    json(response, 200, { status: "ok" });
    return;
  }

  if (request.method === "DELETE" && url.pathname === "/__test__/fixture") {
    fixtures = { ring: ring(), necklace: necklace() };
    json(response, 200, { status: "ok" });
    return;
  }

  const match = /^\/products\/([^/]+)\/$/.exec(url.pathname);

  if (request.method === "GET" && match) {
    const fixture = fixtures[match[1]];
    if (!fixture) {
      json(response, 404, { detail: "Nie znaleziono." });
      return;
    }

    const language = url.searchParams.get("lang") === "en" ? "en" : "pl";
    const currency = url.searchParams.get("currency") === "EUR" ? "EUR" : "PLN";

    json(
      response,
      200,
      localise(fixture.product, fixture, language, currency, origin),
    );
    return;
  }

  json(response, 404, { detail: "Nie znaleziono." });
});

server.listen(port, () => {
  console.log(`Stub API katalogu nasłuchuje na http://localhost:${port}`);
});
