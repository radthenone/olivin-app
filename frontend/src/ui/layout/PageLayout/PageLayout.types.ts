import type { ReactNode } from "react";

export interface LayoutProps {
  children: ReactNode;
  className?: string;
}

export type SlotName = "header" | "side" | "main" | "footer" | string;

export interface SlotConfig {
  name: SlotName;
  colSpan?: number;
  rowSize?: string;
}

export interface LayoutConfig {
  columns: number;
  columnSize?: string;
  slots: SlotConfig[][];
}

export interface WebLayoutProps extends LayoutProps {
  layout?: LayoutConfig;
}
