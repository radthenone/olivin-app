/** Skala odcieni indeksowana liczbowo, np. `colors.brand[500]`. */
export type ColorScale = Record<string, string>;

export interface Colors {
  brand: ColorScale;
  neutral: ColorScale;
  success: ColorScale;
  warning: ColorScale;
  danger: ColorScale;
  info: ColorScale;
}

/** Para: rozmiar czcionki i wysokość linii, w zapisie akceptowanym przez Tailwind. */
export type FontSizeEntry = readonly [size: string, lineHeight: string];

export declare const colors: Colors;
export declare const fontFamily: Record<string, string[]>;
export declare const fontSize: Record<string, FontSizeEntry>;
export declare const fontWeight: Record<string, string>;
export declare const borderRadius: Record<string, string>;
export declare const boxShadow: Record<string, string>;
export declare const screens: Record<string, string>;
export declare const spacing: Record<string, string>;
