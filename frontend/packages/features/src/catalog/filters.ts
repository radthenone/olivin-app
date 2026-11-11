import type {
  ProductsListFineness,
  ProductsListLength,
  ProductsListMaterial,
  ProductsListMetalColor,
  ProductsListParams,
  ProductsListSize,
  ProductsListStone,
} from "@olivin/api/generated/apps/schemas";
import { ProductsListFineness as FinenessValues } from "@olivin/api/generated/apps/schemas/productsListFineness";
import { ProductsListLength as LengthValues } from "@olivin/api/generated/apps/schemas/productsListLength";
import { ProductsListMaterial as MaterialValues } from "@olivin/api/generated/apps/schemas/productsListMaterial";
import { ProductsListMetalColor as MetalColorValues } from "@olivin/api/generated/apps/schemas/productsListMetalColor";
import { ProductsListSize as SizeValues } from "@olivin/api/generated/apps/schemas/productsListSize";
import { ProductsListStone as StoneValues } from "@olivin/api/generated/apps/schemas/productsListStone";

/** Dopuszczalne wartości kruszcu w katalogu. */
export const CATALOG_MATERIALS = Object.values(
  MaterialValues,
) as readonly ProductsListMaterial[];

/** Dopuszczalne próby kruszcu w katalogu. */
export const CATALOG_FINENESSES = Object.values(
  FinenessValues,
) as readonly ProductsListFineness[];

/** Dopuszczalne kolory kruszcu w katalogu. */
export const CATALOG_METAL_COLORS = Object.values(
  MetalColorValues,
) as readonly ProductsListMetalColor[];

/** Dopuszczalne kamienie w katalogu. */
export const CATALOG_STONES = Object.values(
  StoneValues,
) as readonly ProductsListStone[];

/** Dopuszczalne rozmiary pierścionków w katalogu. */
export const CATALOG_SIZES = Object.values(
  SizeValues,
) as readonly ProductsListSize[];

/** Dopuszczalne długości w centymetrach w katalogu. */
export const CATALOG_LENGTHS = Object.values(
  LengthValues,
) as readonly ProductsListLength[];

/** Opcje sortowania listy produktów. */
export const CATALOG_ORDERING_OPTIONS = [
  "newest",
  "price",
  "-price",
  "name",
  "-name",
] as const;

export type CatalogOrdering = (typeof CATALOG_ORDERING_OPTIONS)[number];

export const DEFAULT_CATALOG_ORDERING: CatalogOrdering = "newest";

/**
 * Stan filtrów, wyszukiwania, sortowania i stronicowania widoku katalogu.
 * Ceny `priceMin` i `priceMax` są wyrażone w głównej jednostce waluty klienta (np. PLN).
 */
export interface CatalogFilterState {
  material?: ProductsListMaterial;
  fineness?: ProductsListFineness;
  metalColor?: ProductsListMetalColor;
  stone?: ProductsListStone;
  size?: ProductsListSize;
  length?: ProductsListLength;
  priceMin?: number;
  priceMax?: number;
  search?: string;
  ordering?: CatalogOrdering;
  page?: number;
}

type SearchParamsSource =
  | URLSearchParams
  | Record<string, string | string[] | undefined>
  | string;

function getParamValue(
  source: SearchParamsSource,
  key: string,
): string | undefined {
  if (typeof source === "string") {
    const params = new URLSearchParams(source);
    return params.get(key) ?? undefined;
  }
  if (source instanceof URLSearchParams) {
    return source.get(key) ?? undefined;
  }
  const val = source[key];
  if (Array.isArray(val)) {
    return val[0];
  }
  return val ?? undefined;
}

function parseNumber(value: string | undefined): number | undefined {
  if (!value) return undefined;
  const num = Number(value.trim());
  if (Number.isNaN(num) || num < 0) return undefined;
  return num;
}

function parseInteger(value: string | undefined): number | undefined {
  if (!value) return undefined;
  const num = Number.parseInt(value.trim(), 10);
  if (Number.isNaN(num) || num < 1) return undefined;
  return num;
}

/**
 * Bezpiecznie parsuje parametry zapytania URL do stanu filtrów katalogu.
 *
 * Args:
 *     source: Parametry z URL (URLSearchParams, Record z Next.js searchParams albo string).
 *
 * Returns:
 *     Zweryfikowany stan filtrów. Nieznane lub błędne wartości są pomijane.
 */
export function parseCatalogFilters(
  source: SearchParamsSource,
): CatalogFilterState {
  const state: CatalogFilterState = {};

  const rawMaterial = getParamValue(source, "material");
  if (
    rawMaterial &&
    CATALOG_MATERIALS.includes(rawMaterial as ProductsListMaterial)
  ) {
    state.material = rawMaterial as ProductsListMaterial;
  }

  const rawFineness = getParamValue(source, "fineness");
  if (
    rawFineness &&
    CATALOG_FINENESSES.includes(rawFineness as ProductsListFineness)
  ) {
    state.fineness = rawFineness as ProductsListFineness;
  }

  const rawMetalColor = getParamValue(source, "metalColor");
  if (
    rawMetalColor &&
    CATALOG_METAL_COLORS.includes(rawMetalColor as ProductsListMetalColor)
  ) {
    state.metalColor = rawMetalColor as ProductsListMetalColor;
  }

  const rawStone = getParamValue(source, "stone");
  if (rawStone && CATALOG_STONES.includes(rawStone as ProductsListStone)) {
    state.stone = rawStone as ProductsListStone;
  }

  const rawSize = getParamValue(source, "size");
  if (rawSize && CATALOG_SIZES.includes(rawSize as ProductsListSize)) {
    state.size = rawSize as ProductsListSize;
  }

  const rawLength = getParamValue(source, "length");
  if (rawLength && CATALOG_LENGTHS.includes(rawLength as ProductsListLength)) {
    state.length = rawLength as ProductsListLength;
  }

  const priceMin = parseNumber(getParamValue(source, "priceMin"));
  if (priceMin !== undefined) {
    state.priceMin = priceMin;
  }

  const priceMax = parseNumber(getParamValue(source, "priceMax"));
  if (priceMax !== undefined) {
    state.priceMax = priceMax;
  }

  const rawSearch = getParamValue(source, "search");
  if (rawSearch && rawSearch.trim().length > 0) {
    state.search = rawSearch.trim();
  }

  const rawOrdering = getParamValue(source, "ordering");
  if (
    rawOrdering &&
    CATALOG_ORDERING_OPTIONS.includes(rawOrdering as CatalogOrdering)
  ) {
    state.ordering = rawOrdering as CatalogOrdering;
  }

  const page = parseInteger(getParamValue(source, "page"));
  if (page !== undefined && page > 0) {
    state.page = page;
  }

  return state;
}

/**
 * Serializuje stan filtrów do URLSearchParams.
 *
 * Pomija puste wartości, stronę 1 oraz domyślne sortowanie ('newest').
 *
 * Args:
 *     state: Stan filtrów.
 *
 * Returns:
 *     Nowy obiekt URLSearchParams gotowy do użycia w adresie.
 */
export function serializeCatalogFilters(
  state: CatalogFilterState,
): URLSearchParams {
  const params = new URLSearchParams();

  if (state.material) params.set("material", state.material);
  if (state.fineness) params.set("fineness", state.fineness);
  if (state.metalColor) params.set("metalColor", state.metalColor);
  if (state.stone) params.set("stone", state.stone);
  if (state.size) params.set("size", state.size);
  if (state.length) params.set("length", state.length);
  if (state.priceMin !== undefined)
    params.set("priceMin", String(state.priceMin));
  if (state.priceMax !== undefined)
    params.set("priceMax", String(state.priceMax));
  if (state.search) params.set("search", state.search);
  if (state.ordering && state.ordering !== DEFAULT_CATALOG_ORDERING) {
    params.set("ordering", state.ordering);
  }
  if (state.page !== undefined && state.page > 1) {
    params.set("page", String(state.page));
  }

  return params;
}

/**
 * Mapuje stan filtrów na parametry zapytania API `products_list`.
 * Ceny są przeliczane na grosze (liczby całkowite).
 *
 * Args:
 *     state: Stan filtrów.
 *     options: Dodatkowe opcje (kategoria, kolekcja, pageSize, lang, currency).
 *
 * Returns:
 *     Obiekt parametrów dla `productsList(params)`.
 */
export function toProductsListParams(
  state: CatalogFilterState,
  options?: {
    category?: string;
    collection?: string;
    pageSize?: number;
  },
): ProductsListParams {
  const params: ProductsListParams = {};

  if (options?.category) params.category = options.category;
  if (options?.collection) params.collection = options.collection;
  if (options?.pageSize) params.pageSize = options.pageSize;

  if (state.material) params.material = state.material;
  if (state.fineness) params.fineness = state.fineness;
  if (state.metalColor) params.metalColor = state.metalColor;
  if (state.stone) params.stone = state.stone;
  if (state.size) params.size = state.size;
  if (state.length) params.length = state.length;

  if (state.priceMin !== undefined) {
    params.priceMin = Math.round(state.priceMin * 100);
  }
  if (state.priceMax !== undefined) {
    params.priceMax = Math.round(state.priceMax * 100);
  }

  if (state.search) params.search = state.search;
  if (state.ordering) params.ordering = state.ordering;
  if (state.page) params.page = state.page;

  return params;
}

/**
 * Mapuje parametry `ProductsListParams` z powrotem na `CatalogFilterState`.
 * Ceny przeliczane są z groszy na główną jednostkę (dzielenie przez 100).
 *
 * Args:
 *     params: Parametry API `ProductsListParams`.
 *
 * Returns:
 *     Stan filtrów katalogu.
 */
export function fromProductsListParams(
  params: ProductsListParams,
): CatalogFilterState {
  const state: CatalogFilterState = {};

  if (params.material) state.material = params.material;
  if (params.fineness) state.fineness = params.fineness;
  if (params.metalColor) state.metalColor = params.metalColor;
  if (params.stone) state.stone = params.stone;
  if (params.size) state.size = params.size;
  if (params.length) state.length = params.length;

  if (params.priceMin !== undefined) {
    state.priceMin = params.priceMin / 100;
  }
  if (params.priceMax !== undefined) {
    state.priceMax = params.priceMax / 100;
  }

  if (params.search) state.search = params.search;
  if (
    params.ordering &&
    CATALOG_ORDERING_OPTIONS.includes(params.ordering as CatalogOrdering)
  ) {
    state.ordering = params.ordering as CatalogOrdering;
  }
  if (params.page !== undefined && params.page > 0) {
    state.page = params.page;
  }

  return state;
}

/**
 * Czy w stanie są aktywne jakiekolwiek filtry, wyszukiwanie lub niestandardowe sortowanie.
 */
export function hasActiveFilters(state: CatalogFilterState): boolean {
  return Boolean(
    state.material ||
      state.fineness ||
      state.metalColor ||
      state.stone ||
      state.size ||
      state.length ||
      state.priceMin !== undefined ||
      state.priceMax !== undefined ||
      state.search ||
      (state.ordering && state.ordering !== DEFAULT_CATALOG_ORDERING),
  );
}

/**
 * Aplikuje zmianę filtrów i ZAWSZE resetuje stronę do 1 (kryterium akceptacji).
 *
 * Args:
 *     current: Bieżący stan filtrów.
 *     updates: Częściowe zmiany filtrów (nowa wartość lub `undefined` do usunięcia).
 *
 * Returns:
 *     Nowy stan z zaaplikowanymi zmianami i stroną ustawioną na 1.
 */
export function withFilterChange(
  current: CatalogFilterState,
  updates: Partial<CatalogFilterState>,
): CatalogFilterState {
  const next = { ...current, ...updates };

  // Usuwamy klucze o wartości undefined/puste
  for (const [key, value] of Object.entries(next) as [
    keyof CatalogFilterState,
    unknown,
  ][]) {
    if (value === undefined || value === "") {
      delete next[key];
    }
  }

  // Zmiana filtra ZAWSZE wraca na pierwszą stronę
  next.page = 1;

  return next;
}

/**
 * Czyści wszystkie filtry, wyszukiwanie i sortowanie, resetując widok do pierwszej strony.
 */
export function clearCatalogFilters(
  _current?: CatalogFilterState,
): CatalogFilterState {
  return {};
}
