import { describe, expect, test } from "bun:test";
import { renderToStaticMarkup } from "react-dom/server";
import { useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
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
import { Label } from "@/components/ui/label";

/**
 * Dowód, że pierwsze prymitywy istnieją i renderują to, co widzi użytkownik.
 * Klasy wariantów są sprawdzane tylko po semantycznej roli tokenu (primary,
 * destructive) — reszta wyglądu należy do tokenów i nie jest tu powielana.
 */
describe("ui primitives", () => {
  test("Button renders its label and token-backed variants", () => {
    const html = renderToStaticMarkup(<Button>Zapisz</Button>);

    expect(html).toContain("<button");
    expect(html).toContain("Zapisz");
    expect(html).toContain("bg-primary");

    const destructive = renderToStaticMarkup(
      <Button variant="destructive">Usuń</Button>,
    );

    expect(destructive).toContain("bg-destructive");
  });

  test("Button forwards disabled state", () => {
    const html = renderToStaticMarkup(<Button disabled>Zapisz</Button>);

    expect(html).toContain("disabled");
  });

  test("Input renders a labelled, invalid-aware field", () => {
    const html = renderToStaticMarkup(
      <Input placeholder="ty@example.com" aria-invalid />,
    );

    expect(html).toContain("<input");
    expect(html).toContain('placeholder="ty@example.com"');
    expect(html).toContain('aria-invalid="true"');
  });

  test("Label links to its control", () => {
    const html = renderToStaticMarkup(<Label htmlFor="email">E-mail</Label>);

    expect(html).toContain("<label");
    expect(html).toContain('for="email"');
    expect(html).toContain("E-mail");
  });

  test("Card composes header, content and footer", () => {
    const html = renderToStaticMarkup(
      <Card>
        <CardHeader>
          <CardTitle>Konto</CardTitle>
          <CardDescription>Twoje dane</CardDescription>
        </CardHeader>
        <CardContent>Treść</CardContent>
        <CardFooter>Stopka</CardFooter>
      </Card>,
    );

    expect(html).toContain('data-slot="card"');
    expect(html).toContain("Konto");
    expect(html).toContain("Twoje dane");
    expect(html).toContain("Treść");
    expect(html).toContain("Stopka");
  });

  test("Form wires react-hook-form state into label, control and message", () => {
    function ExampleForm() {
      const form = useForm({ defaultValues: { email: "" } });

      return (
        <Form {...form}>
          <form>
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>E-mail</FormLabel>
                  <FormControl>
                    <Input placeholder="ty@example.com" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          </form>
        </Form>
      );
    }

    const html = renderToStaticMarkup(<ExampleForm />);

    expect(html).toContain("E-mail");
    expect(html).toContain('name="email"');
    expect(html).toMatch(/<label[^>]*for="([^"]+)"[^>]*>E-mail/);
    expect(html).toMatch(/<input[^>]*id="([^"]+)"/);
  });
});
