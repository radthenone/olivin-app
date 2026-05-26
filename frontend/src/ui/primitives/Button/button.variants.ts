import { cva, type VariantProps } from "class-variance-authority";

/**
 * Warianty przycisku w stylu shadcn, ale zgodne z NativeWind.
 *
 * Dlaczego istnieje:
 * wygląd przycisków powinien być deklarowany przez intencję
 * (`variant`, `size`), a nie przez powtarzanie klas na ekranach.
 */
export const buttonVariants = cva(
  "items-center justify-center rounded-md border",
  {
    variants: {
      variant: {
        primary: "border-primary bg-primary",
        secondary: "border-neutral-200 bg-neutral-100",
        outline: "border-neutral-300 bg-transparent",
        ghost: "border-transparent bg-transparent",
        destructive: "border-red-600 bg-red-600",
      },
      size: {
        sm: "h-10 px-3",
        md: "h-12 px-4",
        lg: "h-14 px-5",
      },
      disabled: {
        true: "opacity-50",
        false: "opacity-100",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
      disabled: false,
    },
  },
);

/**
 * Warianty tekstu przycisku dopasowane do wariantu kontenera.
 */
export const buttonTextVariants = cva("font-medium", {
  variants: {
    variant: {
      primary: "text-primary-foreground",
      secondary: "text-neutral-950",
      outline: "text-neutral-950",
      ghost: "text-neutral-950",
      destructive: "text-white",
    },
    size: {
      sm: "text-sm",
      md: "text-base",
      lg: "text-base",
    },
  },
  defaultVariants: {
    variant: "primary",
    size: "md",
  },
});

export type ButtonVariantProps = VariantProps<typeof buttonVariants>;
