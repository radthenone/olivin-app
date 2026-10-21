"use client";

import { useTranslations } from "next-intl";
import { useFormContext } from "react-hook-form";

import type { SignupConsentsValues } from "@olivin/schemas";

import { Checkbox } from "@/components/ui/checkbox";
import {
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";

type ConsentName = "consentTerms" | "consentPrivacy" | "consentMarketing";

const CONSENTS: ConsentName[] = [
  "consentTerms",
  "consentPrivacy",
  "consentMarketing",
];

/**
 * Zgody przy zakładaniu konta.
 *
 * Wymagane zgody pilnuje schemat `@olivin/schemas`, a komponent tylko
 * wyświetla pola i komunikaty. Dzięki temu ten sam fragment obsłuży rejestrację
 * e-mailem i dokończenie konta z Google/Facebook.
 */
export function SignupConsents({ disabled }: { disabled?: boolean }) {
  const t = useTranslations("auth.register");
  const { control } = useFormContext<SignupConsentsValues>();

  return (
    <fieldset className="flex flex-col gap-3">
      <legend className="text-sm font-medium text-neutral-900">
        {t("consentsLegend")}
      </legend>

      {CONSENTS.map((name) => (
        <FormField
          key={name}
          control={control}
          name={name}
          render={({ field }) => (
            <FormItem>
              <div className="flex items-start gap-2">
                <FormControl>
                  <Checkbox
                    checked={field.value}
                    disabled={disabled}
                    name={field.name}
                    onBlur={field.onBlur}
                    onChange={(event) => field.onChange(event.target.checked)}
                    ref={field.ref}
                  />
                </FormControl>
                <FormLabel className="font-normal leading-snug">
                  {t(name)}
                </FormLabel>
              </div>
              <FormMessage />
            </FormItem>
          )}
        />
      ))}
    </fieldset>
  );
}
