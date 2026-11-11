import { describe, expect, test } from "bun:test";
import { routes } from "./routes";

describe("mobile navigation routes", () => {
  test("defines catalog routes correctly", () => {
    expect(routes.home).toBe("/home");
    expect(routes.products).toBe("/products");
    expect(routes.productDetail("gold-ring")).toBe("/products/gold-ring");
  });
});
