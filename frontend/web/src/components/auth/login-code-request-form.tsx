"use client";

import Link from "next/link";
import type { Route } from "next";
import { useLocale, useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";

import { useRequestLoginCode } from "@olivin/features/auth";
import {
  requestLoginCodeFormSchema,
  toRequestLoginCodeBody,
  type RequestLoginCodeFormValues,
} from "@olivin/schemas";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";

/**
 * Zamówienie jednorazowego kodu logowania (#352).
 *
 * Po przyjęciu adresu przez allauth przechodzimy na ekran wpisania kodu —
 * backend trzyma oczekujący etap w sesji, więc ekran kodu nie potrzebuje
 * adresu w adresie strony.
 */
export function LoginCodeRequestForm() {
  const t = useTranslations("auth");
  const locale = useLocale();
  const router = useRouter();
  const requestCode = useRequestLoginCode();
  const form = useForm<RequestLoginCodeFormValues>({
    defaultValues: { email: "" },
  });
  const isPending = requestCode.isPending;

  const rootError = form.formState.errors.root?.message;

  async function onSubmit(values: RequestLoginCodeFormValues) {
    form.clearErrors();

    const parsed = requestLoginCodeFormSchema.safeParse(values);
    if (!parsed.success) {
      form.setError("email", {
        type: "validation",
        message: t("errors.emailInvalid"),
      });
      return;
    }

    try {
      await requestCode.mutateAsync(toRequestLoginCodeBody(parsed.data));
      router.push(`/${locale}/login/code/confirm` as Route);
    } catch {
      form.setError("root", {
        type: "server",
        message: t("loginCode.requestFailed"),
      });
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <h1 className="text-2xl font-semibold text-neutral-900">
            {t("loginCode.title")}
          </h1>
        </CardTitle>
        <CardDescription>{t("loginCode.description")}</CardDescription>
      </CardHeader>

      <CardContent>
        <Form {...form}>
          <form
            className="flex flex-col gap-4"
            noValidate
            onSubmit={form.handleSubmit(onSubmit)}
          >
            <FormField
              control={form.control}
              name="email"
              rules={{ required: t("errors.emailRequired") }}
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("loginCode.email")}</FormLabel>
                  <FormControl>
                    <Input
                      autoComplete="email"
                      disabled={isPending}
                      type="email"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {rootError && (
              <p className="text-sm text-destructive" role="alert">
                {rootError}
              </p>
            )}

            <Button disabled={isPending} type="submit">
              {isPending
                ? t("loginCode.requestSubmitting")
                : t("loginCode.requestSubmit")}
            </Button>

            <Link
              className="text-center text-sm text-neutral-700 underline underline-offset-4"
              href={`/${locale}/login` as Route}
            >
              {t("loginCode.backToPassword")}
            </Link>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
