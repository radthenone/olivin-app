import { describe, expect, test } from "bun:test";
import {
  CATALOG_FINENESSES,
  CATALOG_LENGTHS,
  CATALOG_MATERIALS,
  CATALOG_METAL_COLORS,
  CATALOG_ORDERING_OPTIONS,
  CATALOG_SIZES,
  CATALOG_STONES,
  clearCatalogFilters,
  fromProductsListParams,
  hasActiveFilters,
  parseCatalogFilters,
  serializeCatalogFilters,
  toProductsListParams,
  withFilterChange,
  type CatalogFilterState,
} from "./filters";

describe("Catalog filters URL mapping and products_list params", () => {
  test("parses empty search params to an empty state", () => {
    const state = parseCatalogFilters("");
    expect(state).toEqual({});
    expect(hasActiveFilters(state)).toBe(false);
  });

  test("parses valid filter params from URLSearchParams", () => {
    const params = new URLSearchParams({
      material: "gold",
      fineness: "585",
      metalColor: "yellow",
      stone: "diamond",
      size: "16",
      length: "45",
      priceMin: "150",
      priceMax: "3000",
      search: "  złoty pierścionek  ",
      ordering: "price",
      page: "2",
    });

    const state = parseCatalogFilters(params);

    expect(state).toEqual({
      material: "gold",
      fineness: "585",
      metalColor: "yellow",
      stone: "diamond",
      size: "16",
      length: "45",
      priceMin: 150,
      priceMax: 3000,
      search: "złoty pierścionek",
      ordering: "price",
      page: 2,
    });
    expect(hasActiveFilters(state)).toBe(true);
  });

  test("parses plain object record searchParams", () => {
    const record = {
      material: "silver",
      ordering: "-price",
      page: ["3"],
    };

    const state = parseCatalogFilters(record);

    expect(state.material).toBe("silver");
    expect(state.ordering).toBe("-price");
    expect(state.page).toBe(3);
  });

  test("ignores invalid or unknown enum values and bad numbers", () => {
    const params = new URLSearchParams({
      material: "plastic",
      fineness: "9999",
      metalColor: "blue",
      stone: "glass",
      size: "99",
      length: "1234",
      priceMin: "-10",
      priceMax: "not-a-number",
      ordering: "popularity",
      page: "0",
      search: "   ",
    });

    const state = parseCatalogFilters(params);

    expect(state).toEqual({});
  });

  test("serializes filter state to URLSearchParams", () => {
    const state: CatalogFilterState = {
      material: "gold",
      metalColor: "rose",
      stone: "ruby",
      priceMin: 200,
      priceMax: 1500,
      search: "obrączka",
      ordering: "name",
      page: 4,
    };

    const searchParams = serializeCatalogFilters(state);

    expect(searchParams.get("material")).toBe("gold");
    expect(searchParams.get("metalColor")).toBe("rose");
    expect(searchParams.get("stone")).toBe("ruby");
    expect(searchParams.get("priceMin")).toBe("200");
    expect(searchParams.get("priceMax")).toBe("1500");
    expect(searchParams.get("search")).toBe("obrączka");
    expect(searchParams.get("ordering")).toBe("name");
    expect(searchParams.get("page")).toBe("4");
  });

  test("omits default ordering ('newest') and page 1 from URLSearchParams", () => {
    const state: CatalogFilterState = {
      material: "silver",
      ordering: "newest",
      page: 1,
    };

    const searchParams = serializeCatalogFilters(state);

    expect(searchParams.get("material")).toBe("silver");
    expect(searchParams.has("ordering")).toBe(false);
    expect(searchParams.has("page")).toBe(false);
  });

  test("round-trips state through URLSearchParams", () => {
    const initial: CatalogFilterState = {
      material: "platinum",
      fineness: "950",
      metalColor: "white",
      stone: "sapphire",
      size: "14",
      length: "50",
      priceMin: 500,
      priceMax: 4500,
      search: "wisiorek",
      ordering: "-name",
      page: 3,
    };

    const serialized = serializeCatalogFilters(initial);
    const parsed = parseCatalogFilters(serialized);

    expect(parsed).toEqual(initial);
  });

  test("maps filter state to ProductsListParams (prices in grosze)", () => {
    const state: CatalogFilterState = {
      material: "gold",
      fineness: "585",
      metalColor: "yellow",
      stone: "diamond",
      size: "17",
      length: "45",
      priceMin: 120,
      priceMax: 2500,
      search: "pierścionek",
      ordering: "price",
      page: 2,
    };

    const apiParams = toProductsListParams(state, {
      category: "pierscionki",
      pageSize: 12,
    });

    expect(apiParams).toEqual({
      category: "pierscionki",
      material: "gold",
      fineness: "585",
      metalColor: "yellow",
      stone: "diamond",
      size: "17",
      length: "45",
      priceMin: 12000,
      priceMax: 250000,
      search: "pierścionek",
      ordering: "price",
      page: 2,
      pageSize: 12,
    });
  });

  test("maps ProductsListParams back to CatalogFilterState in both directions", () => {
    const apiParams = {
      category: "kolczyki",
      collection: "lato-2026",
      material: "gold" as const,
      fineness: "585" as const,
      metalColor: "white" as const,
      stone: "emerald" as const,
      size: "12" as const,
      length: "40" as const,
      priceMin: 15000,
      priceMax: 80000,
      search: "szmaragd",
      ordering: "-price",
      page: 2,
    };

    const state = fromProductsListParams(apiParams);

    expect(state).toEqual({
      material: "gold",
      fineness: "585",
      metalColor: "white",
      stone: "emerald",
      size: "12",
      length: "40",
      priceMin: 150,
      priceMax: 800,
      search: "szmaragd",
      ordering: "-price",
      page: 2,
    });

    // Powrót do apiParams
    const backToApi = toProductsListParams(state, {
      category: apiParams.category,
      collection: apiParams.collection,
    });

    expect(backToApi.priceMin).toBe(15000);
    expect(backToApi.priceMax).toBe(80000);
    expect(backToApi.material).toBe("gold");
  });

  test("withFilterChange updates filter and resets page to 1", () => {
    const current: CatalogFilterState = {
      material: "gold",
      page: 3,
    };

    const updated = withFilterChange(current, { metalColor: "rose" });

    expect(updated).toEqual({
      material: "gold",
      metalColor: "rose",
      page: 1,
    });
  });

  test("clearCatalogFilters empties all filters and resets page", () => {
    const current: CatalogFilterState = {
      material: "gold",
      metalColor: "rose",
      priceMin: 100,
      search: "złoto",
      ordering: "price",
      page: 5,
    };

    const cleared = clearCatalogFilters(current);

    expect(cleared).toEqual({});
    expect(hasActiveFilters(cleared)).toBe(false);
  });

  test("exports constants for catalog filters", () => {
    expect(CATALOG_MATERIALS).toContain("gold");
    expect(CATALOG_FINENESSES).toContain("585");
    expect(CATALOG_METAL_COLORS).toContain("yellow");
    expect(CATALOG_STONES).toContain("diamond");
    expect(CATALOG_SIZES).toContain("17");
    expect(CATALOG_LENGTHS).toContain("45");
    expect(CATALOG_ORDERING_OPTIONS).toContain("price");
  });
});
