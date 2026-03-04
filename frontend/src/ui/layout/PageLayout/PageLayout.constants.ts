import type { LayoutConfig } from "./PageLayout.types";

export const LAYOUT_CONSTANTS: LayoutConfig = {
  columns: 3,
  columnSize: "1fr",
  slots: [
    [{ name: "header", colSpan: 3, rowSize: "80px" }],
    [
      { name: "side", colSpan: 1, rowSize: "1fr" },
      { name: "main", colSpan: 2 },
    ],
    [{ name: "footer", colSpan: 3, rowSize: "60px" }],
  ],
};
