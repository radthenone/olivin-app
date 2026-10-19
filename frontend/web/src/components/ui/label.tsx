import * as React from "react";

import { cn } from "@/lib/utils";

/**
 * Etykieta formularza. Natywny `label` wiąże się z kontrolką przez `htmlFor`,
 * więc cały kontrakt dostępności zostaje w HTML — bez zależności od Radix.
 */
function Label({ className, ...props }: React.ComponentProps<"label">) {
  return (
    <label
      data-slot="label"
      className={cn(
        "flex select-none items-center gap-2 text-sm font-medium leading-none group-data-[disabled=true]:pointer-events-none peer-disabled:cursor-not-allowed peer-disabled:opacity-50",
        className,
      )}
      {...props}
    />
  );
}

export { Label };
