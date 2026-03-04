import type { LayoutConfig } from "./PageLayout.types";

export function generateGridStyles(config: LayoutConfig) {
  const gridTemplateColumns = `repeat(${config.columns}, ${config.columnSize ?? "1fr"})`;

  const gridTemplateRows = config.slots
    .map((row) => row[0]?.rowSize ?? "1fr")
    .join(" ");

  const gridTemplateAreas = config.slots
    .map((row) => {
      const cells = row.flatMap((slot) =>
        Array(slot.colSpan ?? 1).fill(slot.name),
      );
      return `'${cells.join(" ")}'`;
    })
    .join(" ");

  return { gridTemplateColumns, gridTemplateRows, gridTemplateAreas };
}
