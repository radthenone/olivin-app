export type Align = "start" | "center" | "end" | "stretch" | "baseline";
export type Justify =
  | "start"
  | "center"
  | "end"
  | "between"
  | "around"
  | "evenly";
export type Direction = "row" | "col";
export type Gap = 0 | 1 | 2 | 3 | 4 | 5 | 6 | 8 | 10 | 12 | 16;

export type ContainerStyleProps = {
  platform?: "web" | "native";
  direction?: Direction;
  align?: Align;
  justify?: Justify;
  wrap?: boolean;
  gap?: Gap;
};
