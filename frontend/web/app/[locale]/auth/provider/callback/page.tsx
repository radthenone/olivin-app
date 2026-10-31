import { Suspense } from "react";

import { ProviderCallback } from "@/components/auth/provider-callback";

/**
 * Strona powrotu z Google/Facebook pod prefiksem języka (#355).
 *
 * Plik trasy tylko komponuje sekcję; `Suspense` jest potrzebny dla odczytu
 * parametrów zapytania w komponencie klienta.
 */
export default function ProviderCallbackPage() {
  return (
    <main className="mx-auto w-full max-w-md px-6 py-16">
      <Suspense fallback={null}>
        <ProviderCallback />
      </Suspense>
    </main>
  );
}
