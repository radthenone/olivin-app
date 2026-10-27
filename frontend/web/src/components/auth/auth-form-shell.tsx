"use client";

import Link from "next/link";
import type { Route } from "next";
import type { Control, FieldPath, FieldValues } from "react-hook-form";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";

/**
 * Szkielet ekranów auth (#406): karta z nagłówkiem h1, opis i treść formularza.
 */
export function AuthFormCard({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <h1 className="text-2xl font-semibold text-neutral-900">{title}</h1>
        </CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>

      <CardContent>{children}</CardContent>
    </Card>
  );
}

/** Błąd całego formularza; bez komunikatu nic nie renderuje. */
export function AuthFormError({ message }: { message?: string }) {
  if (!message) {
    return null;
  }

  return (
    <p className="text-sm text-destructive" role="alert">
      {message}
    </p>
  );
}

/** Przycisk wysyłki, który w trakcie żądania pokazuje etykietę pending. */
export function AuthSubmitButton({
  isPending,
  label,
  pendingLabel,
}: {
  isPending: boolean;
  label: string;
  pendingLabel: string;
}) {
  return (
    <Button disabled={isPending} type="submit">
      {isPending ? pendingLabel : label}
    </Button>
  );
}

/** Link pomocniczy pod formularzem (np. powrót do logowania hasłem). */
export function AuthFormLink({
  href,
  children,
}: {
  href: Route;
  children: React.ReactNode;
}) {
  return (
    <Link
      className="text-center text-sm text-neutral-700 underline underline-offset-4"
      href={href}
    >
      {children}
    </Link>
  );
}

/** Pole jednorazowego kodu z e-maila; wspólne dla potwierdzenia logowania i e-maila. */
export function AuthCodeField<T extends FieldValues>({
  control,
  name,
  label,
  disabled,
}: {
  control: Control<T>;
  name: FieldPath<T>;
  label: string;
  disabled: boolean;
}) {
  return (
    <FormField
      control={control}
      name={name}
      render={({ field }) => (
        <FormItem>
          <FormLabel>{label}</FormLabel>
          <FormControl>
            <Input
              autoComplete="one-time-code"
              disabled={disabled}
              {...field}
            />
          </FormControl>
          <FormMessage />
        </FormItem>
      )}
    />
  );
}
