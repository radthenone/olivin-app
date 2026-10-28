import { describe, expect, test } from "bun:test";
import { renderToStaticMarkup } from "react-dom/server";

import {
  AuthFormCard,
  AuthFormError,
  AuthFormLink,
  AuthSubmitButton,
} from "./auth-form-shell";

/**
 * Wspólny szkielet ekranów auth (#406).
 *
 * Karta z nagłówkiem h1, błąd formularza z `role="alert"` i link pomocniczy
 * mają jeden wygląd we wszystkich formularzach kodu. Testujemy markup, bo
 * komponenty są czyste i nie potrzebują przeglądarki.
 */
describe("AuthFormCard", () => {
  test("renders the title as an h1 with the description below it", () => {
    const markup = renderToStaticMarkup(
      <AuthFormCard title="Zaloguj kodem" description="Podaj adres e-mail">
        <p>treść</p>
      </AuthFormCard>,
    );

    expect(markup).toContain("<h1");
    expect(markup).toContain("Zaloguj kodem");
    expect(markup).toContain("Podaj adres e-mail");
    expect(markup).toContain("<p>treść</p>");
  });
});

describe("AuthFormError", () => {
  test("renders an alert with the message when one is set", () => {
    const markup = renderToStaticMarkup(
      <AuthFormError message="Kod nie pasuje" />,
    );

    expect(markup).toContain('role="alert"');
    expect(markup).toContain("Kod nie pasuje");
  });

  test("renders nothing when there is no message", () => {
    expect(renderToStaticMarkup(<AuthFormError message={undefined} />)).toBe(
      "",
    );
  });
});

describe("AuthSubmitButton", () => {
  test("shows the pending label and disables itself while submitting", () => {
    const markup = renderToStaticMarkup(
      <AuthSubmitButton
        isPending
        label="Wyślij kod"
        pendingLabel="Wysyłanie..."
      />,
    );

    expect(markup).toContain("Wysyłanie...");
    expect(markup).toContain('disabled=""');
    expect(markup).toContain('type="submit"');
  });

  test("shows the idle label when not pending", () => {
    const markup = renderToStaticMarkup(
      <AuthSubmitButton
        isPending={false}
        label="Wyślij kod"
        pendingLabel="Wysyłanie..."
      />,
    );

    expect(markup).toContain("Wyślij kod");
    expect(markup).not.toContain('disabled=""');
  });
});

describe("AuthFormLink", () => {
  test("renders a helper link with the shared text classes", () => {
    const markup = renderToStaticMarkup(
      <AuthFormLink href="/pl/login">Wróć do hasła</AuthFormLink>,
    );

    expect(markup).toContain('href="/pl/login"');
    expect(markup).toContain(
      "text-center text-sm text-neutral-700 underline underline-offset-4",
    );
    expect(markup).toContain("Wróć do hasła");
  });
});
