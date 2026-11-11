import { describe, expect, test } from "bun:test";

import { uniqueStones } from "./product-stones";

describe("uniqueStones", () => {
  test("deduplicates stones across variants keeping first-seen order", () => {
    expect(
      uniqueStones([
        { stone: "ruby" },
        { stone: "diamond" },
        { stone: "ruby" },
      ]),
    ).toEqual(["ruby", "diamond"]);
  });

  test("returns an empty list without variants", () => {
    expect(uniqueStones([])).toEqual([]);
  });
});
