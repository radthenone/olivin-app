"use client";

import { useForm } from "react-hook-form";
import { useTranslations } from "next-intl";

import {
  mapLoginErrors,
  useLogin,
  type LoginError,
} from "@olivin/features/auth";

import { loginErrorsFromFailure } from "./login-errors";

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

type LoginFormValues = {
  email: string;
  password: string;
};

/**
 * Formularz logowania e-mailem i hasłem.
 *
 * Sekcja domenowa: zna hooki auth i katalog tekstów, a wygląd składa wyłącznie
 * z komponentów `ui/`. Plik trasy tylko ją umieszcza na stronie.
 */
export function LoginForm() {
  const t = useTranslations("auth");
  const { login, isPending } = useLogin();
  const form = useForm<LoginFormValues>({
    defaultValues: { email: "", password: "" },
  });

  const rootError = form.formState.errors.root?.message;

  function errorMessage(error: LoginError): string {
    if (error.code === "invalidCredentials") {
      return t("errors.invalidCredentials");
    }

    if (error.code === "tooManyAttempts") {
      return t("errors.tooManyAttempts");
    }

    return error.message ?? t("errors.generic");
  }

  async function onSubmit(values: LoginFormValues) {
    form.clearErrors();

    try {
      const response = await login(values);

      if (response.status === 200) {
        form.reset();
        return;
      }

      showErrors(mapLoginErrors(response.data));
    } catch (error) {
      // Backend może odrzucić logowanie błędem 400 z listą pól — wtedy
      // pokazujemy je przy właściwych polach, a nie jako ogólny komunikat.
      const fieldErrors = loginErrorsFromFailure(error);
      if (fieldErrors) {
        showErrors(fieldErrors);
        return;
      }

      form.setError("root", { type: "server", message: t("errors.generic") });
    }
  }

  function showErrors(errors: LoginError[]) {
    for (const error of errors) {
      form.setError(error.target === "form" ? "root" : error.target, {
        type: "server",
        message: errorMessage(error),
      });
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>
          <h1 className="text-2xl font-semibold text-neutral-900">
            {t("login.title")}
          </h1>
        </CardTitle>
        <CardDescription>{t("login.description")}</CardDescription>
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
              rules={{
                required: t("errors.emailRequired"),
                pattern: {
                  value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                  message: t("errors.emailInvalid"),
                },
              }}
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("login.email")}</FormLabel>
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

            <FormField
              control={form.control}
              name="password"
              rules={{ required: t("errors.passwordRequired") }}
              render={({ field }) => (
                <FormItem>
                  <FormLabel>{t("login.password")}</FormLabel>
                  <FormControl>
                    <Input
                      autoComplete="current-password"
                      disabled={isPending}
                      type="password"
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
              {isPending ? t("login.submitting") : t("login.submit")}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}
