import { describe, expect, test } from "bun:test";
import type {
  ProductVariant,
  StoneEnum,
} from "@olivin/api/generated/apps/schemas";
import { messages, type Locale } from "@olivin/i18n";
import { NextIntlClientProvider } from "next-intl";
import type { ComponentProps } from "react";
import { renderToStaticMarkup } from "react-dom/server";

import { VariantSelector } from "./variant-selector";

function mockVariant(
  sku: string,
  overrides: Partial<ProductVariant> = {},
): ProductVariant {
  return {
    id: sku,
    sku,
    available: 5,
    isAvailable: true,
    isLowStock: false,
    metalColor: "yellow",
    size: "17",
    length: "45",
    stone: "diamond",
    metalWeightGrams: "3.5",
    price: { amount: 100_000, currency: "PLN" },
    vatRate: "0.2300",
    isVatExempt: false,
    vatExemptionBasis: "",
    images: [],
    gemstones: [],
    ...overrides,
  };
}

/** Selektor korzysta z `next-intl`, więc potrzebuje dostawcy komunikatów. */
function render(
  props: ComponentProps<typeof VariantSelector>,
  locale: Locale = "pl",
): string {
  return renderToStaticMarkup(
    <NextIntlClientProvider
      locale={locale}
      messages={messages[locale]}
      timeZone="Europe/Warsaw"
    >
      <VariantSelector {...props} />
    </NextIntlClientProvider>,
  );
}

/** Znaczniki przycisków radio w kolejności występowania w markupie. */
function radios(markup: string): string[] {
  return markup.match(/<button[^>]*role="radio"[^>]*>/g) ?? [];
}

describe("VariantSelector", () => {
  const v1 = mockVariant("V1", {
    metalColor: "yellow",
    size: "16",
    isAvailable: true,
  });
  const v2 = mockVariant("V2", {
    metalColor: "yellow",
    size: "17",
    isAvailable: true,
  });
  const v3 = mockVariant("V3", {
    metalColor: "white",
    size: "17",
    isAvailable: false,
  });
  const variants = [v1, v2, v3];

  test("renders radiogroups for attributes with many values", () => {
    const markup = render({
      selectedAttributes: { metalColor: "yellow", size: "16" },
      variants,
    });

    expect(markup.match(/role="radiogroup"/g)).toHaveLength(2);
    expect(markup).toContain('role="radio"');
    expect(markup).toContain("Żółte złoto");
    expect(markup).toContain("Białe złoto");
  });

  test("shows an attribute with a single value read-only", () => {
    const markup = render({
      selectedAttributes: { metalColor: "yellow", size: "16" },
      variants,
    });

    // Długość (45) i kamień (diament) są takie same we wszystkich wariantach.
    expect(markup).toContain("Długość:");
    expect(markup).toContain("45 cm");
    expect(markup).toContain("Diament");
    expect(radios(markup).join("")).not.toContain("45 cm");
    expect(radios(markup).join("")).not.toContain("Diament");
  });

  test("marks selected option with aria-checked=true", () => {
    const markup = render({
      selectedAttributes: { metalColor: "yellow", size: "16" },
      variants,
    });

    expect(markup.match(/aria-checked="true"/g)).toHaveLength(2);
  });

  test("does not disable an option whose combination does not exist", () => {
    // Zaznaczone: żółte, 16. Kombinacja (białe, 16) nie istnieje, ale klik ma
    // przeskoczyć do (białe, 17), więc opcja nie jest zablokowana.
    const markup = render({
      selectedAttributes: { metalColor: "yellow", size: "16" },
      variants,
    });

    // Klasa `disabled:` Tailwinda jest w markupie zawsze, więc szukamy atrybutów.
    expect(markup).not.toContain('disabled=""');
    expect(markup).not.toContain("aria-disabled");
    expect(radios(markup)).toHaveLength(4);
  });

  test("marks an option leading to an out-of-stock variant as unavailable", () => {
    // Białe istnieje tylko jako (białe, 17) z isAvailable=false.
    const markup = render({
      selectedAttributes: { metalColor: "yellow", size: "17" },
      variants,
    });

    expect(markup).toContain('aria-label="Białe złoto (Niedostępny)"');
    expect(markup).toContain('aria-label="Żółte złoto"');
  });

  test("uses a roving tabindex with the selected option as the only tab stop", () => {
    const markup = render({
      selectedAttributes: { metalColor: "white", size: "17" },
      variants,
    });

    const byLabel = (label: string) =>
      radios(markup).find((tag) => tag.includes(`aria-label="${label}`)) ?? "";

    expect(byLabel("Białe złoto")).toContain('tabindex="0"');
    expect(byLabel("Żółte złoto")).toContain('tabindex="-1"');
    expect(byLabel("17")).toContain('tabindex="0"');
    expect(byLabel("16")).toContain('tabindex="-1"');
  });

  test("makes the first option the tab stop when nothing is selected", () => {
    const markup = render({ selectedAttributes: {}, variants });

    const tabIndexes = radios(markup).map(
      (tag) => /tabindex="(-?\d)"/.exec(tag)?.[1],
    );

    // Dwie grupy po dwie opcje: pierwsza opcja każdej grupy jest w kolejności Tab.
    expect(tabIndexes).toEqual(["0", "-1", "0", "-1"]);
  });

  test("offers a 'none' option for an attribute present in only some variants", () => {
    const withStone = mockVariant("A", { stone: "diamond" });
    const withoutStone = mockVariant("B", {
      stone: "" as unknown as StoneEnum,
    });
    const markup = render({
      selectedAttributes: { metalColor: "yellow", size: "17", stone: "" },
      variants: [withStone, withoutStone],
    });

    expect(markup).toContain('aria-label="Diament"');
    expect(markup).toContain('aria-label="Brak"');
  });

  test("renders labels in the requested language", () => {
    const markup = render(
      { selectedAttributes: { metalColor: "yellow", size: "16" }, variants },
      "en",
    );

    expect(markup).toContain("Yellow gold");
    expect(markup).toContain("White gold");
    expect(markup).toContain("Length:");
    expect(markup).toContain("45 cm");
  });
});
