import { describe, expect, test } from "bun:test";

import { checkSource } from "./check-ui-purity.mjs";

const file = "src/components/ui/button.tsx";

describe("checkSource", () => {
  test("rejects hex colors", () => {
    const violations = checkSource('const className = "bg-[#ffffff]";', file);

    expect(violations).toHaveLength(1);
    expect(violations[0].reason).toBe("hex color");
  });

  test("rejects arbitrary values with a number", () => {
    const violations = checkSource(
      'const className = "w-[13px] p-[3px] text-[14px]";',
      file,
    );

    expect(violations.map((violation) => violation.reason)).toEqual([
      "arbitrary numeric value",
      "arbitrary numeric value",
      "arbitrary numeric value",
    ]);
  });

  test("rejects arbitrary color values", () => {
    const violations = checkSource(
      'const className = "bg-[rgb(0_0_0)] text-[oklch(0.5_0.1_20)]";',
      file,
    );

    expect(violations.map((violation) => violation.reason)).toEqual([
      "arbitrary color value",
      "arbitrary color value",
    ]);
  });

  test("rejects named colors in arbitrary values", () => {
    const violations = checkSource(
      'const className = "bg-[red] text-[white] border-x-[transparent]";',
      file,
    );

    expect(violations.map((violation) => violation.reason)).toEqual([
      "arbitrary color value",
      "arbitrary color value",
      "arbitrary color value",
    ]);
  });

  test("allows keyword arbitrary values outside color utilities", () => {
    expect(checkSource('const className = "w-[auto]";', file)).toEqual([]);
  });

  test("allows data and aria state variants", () => {
    const source = `
      const className =
        "data-[state=open]:bg-accent aria-[invalid=true]:border-danger data-[size=default]:h-9";
    `;

    expect(checkSource(source, file)).toEqual([]);
  });

  test("allows arbitrary selectors that are not values", () => {
    const source = `
      const className = "[&>svg]:size-4 [&_svg:not([class*='size-'])]:size-4";
    `;

    expect(checkSource(source, file)).toEqual([]);
  });

  test("reports the line of each violation", () => {
    const source = 'const ok = "text-sm";\nconst bad = "w-[13px]";';

    const violations = checkSource(source, file);

    expect(violations).toHaveLength(1);
    expect(violations[0].line).toBe(2);
    expect(violations[0].file).toBe(file);
  });
});
