import * as React from "react";

import { cn } from "@/lib/utils";

/**
 * Natywny checkbox w stylach tokenów.
 *
 * Zgody wymagają prawdziwego `input[type=checkbox]`, żeby klawiatura, czytniki
 * ekranu i `FormField` działały bez dodatkowej zależności.
 */
function Checkbox({ className, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      type="checkbox"
      data-slot="checkbox"
      className={cn(
        "size-4 shrink-0 cursor-pointer rounded-sm border border-input accent-primary outline-none disabled:cursor-not-allowed disabled:opacity-50 focus-visible:ring-2 focus-visible:ring-ring/50 aria-invalid:border-destructive",
        className,
      )}
      {...props}
    />
  );
}

export { Checkbox };
