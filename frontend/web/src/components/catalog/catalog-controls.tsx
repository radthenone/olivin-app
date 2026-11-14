"use client";

import { useState, type ChangeEvent, type FormEvent } from "react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import type { Route } from "next";
import { useTranslations } from "next-intl";
import {
  CATALOG_FINENESSES,
  CATALOG_LENGTHS,
  CATALOG_MATERIALS,
  CATALOG_METAL_COLORS,
  CATALOG_PRICE_MAX,
  CATALOG_SIZES,
  CATALOG_STONES,
  hasActiveFilters,
  parseCatalogPrice,
  serializeCatalogFilters,
  withFilterChange,
  type CatalogFilterState,
  type CatalogOrdering,
} from "@olivin/features/catalog";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

const selectClassName =
  "flex h-9 w-full min-w-0 rounded-md border border-input bg-transparent px-3 py-1 text-base shadow-xs outline-none transition-[color,box-shadow] focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/50 disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50 md:text-sm text-foreground";

/**
 * Pole tekstowe zsynchronizowane z wartością z adresu.
 *
 * Zmiana wartości z adresu (wyczyszczenie, „wstecz”) nadpisuje wpisany tekst.
 * Stan jest korygowany w trakcie renderu, a nie przez `key`: remont zgubiłby
 * fokus po zatwierdzeniu formularza.
 */
function useUrlSyncedInput(urlValue: string) {
  const [value, setValue] = useState(urlValue);
  const [syncedUrlValue, setSyncedUrlValue] = useState(urlValue);

  if (syncedUrlValue !== urlValue) {
    setSyncedUrlValue(urlValue);
    setValue(urlValue);
  }

  return [value, setValue] as const;
}

/**
 * Pasek wyszukiwania w katalogu produktów (#360).
 */
export function CatalogSearch({
  initialSearch = "",
  basePath,
  currentFilters = {},
}: {
  initialSearch?: string;
  basePath: string;
  currentFilters?: CatalogFilterState;
}) {
  const t = useTranslations("catalog");
  const router = useRouter();
  const pathname = usePathname() || basePath;
  const [searchTerm, setSearchTerm] = useUrlSyncedInput(initialSearch);

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const nextState = withFilterChange(currentFilters, {
      search: searchTerm.trim() || undefined,
    });
    const query = serializeCatalogFilters(nextState).toString();
    router.push((query ? `${pathname}?${query}` : pathname) as Route);
  };

  const handleClear = () => {
    setSearchTerm("");
    const nextState = withFilterChange(currentFilters, { search: undefined });
    const query = serializeCatalogFilters(nextState).toString();
    router.push((query ? `${pathname}?${query}` : pathname) as Route);
  };

  return (
    <form
      role="search"
      aria-label={t("search.label")}
      onSubmit={handleSubmit}
      className="flex w-full max-w-md items-center gap-2"
    >
      <div className="relative flex-1">
        <Label htmlFor="catalog-search" className="sr-only">
          {t("search.label")}
        </Label>
        <Input
          id="catalog-search"
          type="search"
          name="search"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          placeholder={t("search.placeholder")}
        />
      </div>
      <Button type="submit">{t("search.submit")}</Button>
      {Boolean(initialSearch) && (
        <Button type="button" variant="ghost" onClick={handleClear}>
          {t("search.clear")}
        </Button>
      )}
    </form>
  );
}

/**
 * Przełącznik sortowania produktów w katalogu (#360).
 */
export function CatalogSort({
  currentOrdering,
  basePath,
  currentFilters = {},
}: {
  currentOrdering?: CatalogOrdering;
  basePath: string;
  currentFilters?: CatalogFilterState;
}) {
  const t = useTranslations("catalog");
  const router = useRouter();
  const pathname = usePathname() || basePath;

  const handleChange = (event: ChangeEvent<HTMLSelectElement>) => {
    const nextOrdering = event.target.value as CatalogOrdering;
    const nextState = withFilterChange(currentFilters, {
      ordering: nextOrdering === "newest" ? undefined : nextOrdering,
    });
    const query = serializeCatalogFilters(nextState).toString();
    router.push((query ? `${pathname}?${query}` : pathname) as Route);
  };

  return (
    <div className="flex items-center gap-2">
      <Label
        htmlFor="catalog-sort"
        className="whitespace-nowrap text-sm font-medium text-neutral-700"
      >
        {t("sort.label")}
      </Label>
      <select
        id="catalog-sort"
        name="ordering"
        value={currentOrdering ?? "newest"}
        onChange={handleChange}
        className={cn(selectClassName, "w-auto")}
      >
        <option value="newest">{t("sort.newest")}</option>
        <option value="price">{t("sort.priceAsc")}</option>
        <option value="-price">{t("sort.priceDesc")}</option>
        <option value="name">{t("sort.nameAsc")}</option>
        <option value="-name">{t("sort.nameDesc")}</option>
      </select>
    </div>
  );
}

/**
 * Panel filtrów produktów (atrybuty i przedział ceny) (#360).
 */
export function CatalogFiltersPanel({
  currentFilters = {},
  basePath,
  currency = "PLN",
}: {
  currentFilters?: CatalogFilterState;
  basePath: string;
  /** Kod waluty w etykiecie przedziału ceny; filtry cenowe API są na razie w złotych. */
  currency?: string;
}) {
  const t = useTranslations("catalog");
  const router = useRouter();
  const pathname = usePathname() || basePath;

  const [priceMinInput, setPriceMinInput] = useUrlSyncedInput(
    currentFilters.priceMin !== undefined
      ? String(currentFilters.priceMin)
      : "",
  );
  const [priceMaxInput, setPriceMaxInput] = useUrlSyncedInput(
    currentFilters.priceMax !== undefined
      ? String(currentFilters.priceMax)
      : "",
  );

  const active = hasActiveFilters(currentFilters);

  const updateFilter = (updates: Partial<CatalogFilterState>) => {
    const nextState = withFilterChange(currentFilters, updates);
    const query = serializeCatalogFilters(nextState).toString();
    router.push((query ? `${pathname}?${query}` : pathname) as Route);
  };

  const handlePriceSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    updateFilter({
      priceMin: parseCatalogPrice(priceMinInput),
      priceMax: parseCatalogPrice(priceMaxInput),
    });
  };

  return (
    <div className="flex flex-col gap-5 rounded-xl border border-neutral-200 bg-neutral-0 p-4">
      <div className="flex items-center justify-between border-b border-neutral-200 pb-3">
        <h2 className="text-sm font-semibold uppercase tracking-wider text-neutral-500">
          {t("filters.heading")}
        </h2>
        {active && (
          <Button asChild size="sm" variant="ghost">
            <Link href={basePath as Route}>{t("filters.clear")}</Link>
          </Button>
        )}
      </div>

      <div className="flex flex-col gap-4 text-sm">
        {/* Kruszec */}
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="filter-material">{t("filters.material")}</Label>
          <select
            id="filter-material"
            value={currentFilters.material ?? ""}
            onChange={(e) =>
              updateFilter({
                material:
                  (e.target.value as CatalogFilterState["material"]) ||
                  undefined,
              })
            }
            className={selectClassName}
          >
            <option value="">{t("filters.all")}</option>
            {CATALOG_MATERIALS.map((mat) => (
              <option key={mat} value={mat}>
                {t(`material.${mat}`)}
              </option>
            ))}
          </select>
        </div>

        {/* Kolor kruszcu */}
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="filter-metal-color">{t("filters.metalColor")}</Label>
          <select
            id="filter-metal-color"
            value={currentFilters.metalColor ?? ""}
            onChange={(e) =>
              updateFilter({
                metalColor:
                  (e.target.value as CatalogFilterState["metalColor"]) ||
                  undefined,
              })
            }
            className={selectClassName}
          >
            <option value="">{t("filters.all")}</option>
            {CATALOG_METAL_COLORS.map((col) => (
              <option key={col} value={col}>
                {t(`metalColor.${col}`)}
              </option>
            ))}
          </select>
        </div>

        {/* Próba kruszcu */}
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="filter-fineness">{t("filters.fineness")}</Label>
          <select
            id="filter-fineness"
            value={currentFilters.fineness ?? ""}
            onChange={(e) =>
              updateFilter({
                fineness:
                  (e.target.value as CatalogFilterState["fineness"]) ||
                  undefined,
              })
            }
            className={selectClassName}
          >
            <option value="">{t("filters.all")}</option>
            {CATALOG_FINENESSES.map((fine) => (
              <option key={fine} value={fine}>
                {fine}
              </option>
            ))}
          </select>
        </div>

        {/* Kamień */}
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="filter-stone">{t("filters.stone")}</Label>
          <select
            id="filter-stone"
            value={currentFilters.stone ?? ""}
            onChange={(e) =>
              updateFilter({
                stone:
                  (e.target.value as CatalogFilterState["stone"]) || undefined,
              })
            }
            className={selectClassName}
          >
            <option value="">{t("filters.all")}</option>
            {CATALOG_STONES.map((stone) => (
              <option key={stone} value={stone}>
                {t(`stone.${stone}`)}
              </option>
            ))}
          </select>
        </div>

        {/* Rozmiar */}
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="filter-size">{t("filters.size")}</Label>
          <select
            id="filter-size"
            value={currentFilters.size ?? ""}
            onChange={(e) =>
              updateFilter({
                size:
                  (e.target.value as CatalogFilterState["size"]) || undefined,
              })
            }
            className={selectClassName}
          >
            <option value="">{t("filters.all")}</option>
            {CATALOG_SIZES.map((sz) => (
              <option key={sz} value={sz}>
                {sz}
              </option>
            ))}
          </select>
        </div>

        {/* Długość */}
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="filter-length">{t("filters.length")}</Label>
          <select
            id="filter-length"
            value={currentFilters.length ?? ""}
            onChange={(e) =>
              updateFilter({
                length:
                  (e.target.value as CatalogFilterState["length"]) || undefined,
              })
            }
            className={selectClassName}
          >
            <option value="">{t("filters.all")}</option>
            {CATALOG_LENGTHS.map((len) => (
              <option key={len} value={len}>
                {t("product.lengthValue", { value: len })}
              </option>
            ))}
          </select>
        </div>

        {/* Przedział ceny */}
        <form onSubmit={handlePriceSubmit} className="pt-2">
          <fieldset className="flex min-w-0 flex-col gap-2">
            <legend className="mb-2 font-medium text-neutral-700">
              {t("filters.priceInCurrency", { currency })}
            </legend>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <Label htmlFor="filter-price-min" className="sr-only">
                  {t("filters.priceFrom")}
                </Label>
                <Input
                  id="filter-price-min"
                  type="number"
                  min="0"
                  max={CATALOG_PRICE_MAX}
                  step="0.01"
                  placeholder={t("filters.priceFrom")}
                  value={priceMinInput}
                  onChange={(e) => setPriceMinInput(e.target.value)}
                />
              </div>
              <div>
                <Label htmlFor="filter-price-max" className="sr-only">
                  {t("filters.priceTo")}
                </Label>
                <Input
                  id="filter-price-max"
                  type="number"
                  min="0"
                  max={CATALOG_PRICE_MAX}
                  step="0.01"
                  placeholder={t("filters.priceTo")}
                  value={priceMaxInput}
                  onChange={(e) => setPriceMaxInput(e.target.value)}
                />
              </div>
            </div>
            <Button type="submit" size="sm" variant="outline" className="mt-1">
              {t("filters.apply")}
            </Button>
          </fieldset>
        </form>
      </div>
    </div>
  );
}
