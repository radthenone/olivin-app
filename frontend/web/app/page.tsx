"use client";

import { useHealthRetrieve } from "@olivin/api/generated/apps/health/health";

/**
 * Jedyna trasa aplikacji webowej na tym etapie.
 *
 * Nie jest to strona marketingowa, tylko dowód: pełna ścieżka od bazy danych,
 * przez Django, pakiet klienta API i transport przeglądarkowy, aż po piksel.
 * Dopóki ta strona nie pokaże stanu backendu, twierdzenie o podłączonym
 * backendzie pozostaje nieudowodnione.
 */
export default function HomePage() {
  const health = useHealthRetrieve();

  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col justify-center gap-8 px-6 py-16">
      <header className="flex flex-col gap-2">
        <h1 className="text-4xl font-semibold text-brand-600">Olivin</h1>
        <p className="text-base text-neutral-600">
          Sklep jubilerski. Katalog, koszyk i kasa powstaną w kolejnych krokach.
        </p>
      </header>

      <section
        aria-labelledby="stan-backendu"
        className="rounded-lg border border-neutral-200 bg-neutral-0 p-6 shadow-sm"
      >
        <h2
          id="stan-backendu"
          className="text-sm font-semibold uppercase tracking-wide text-neutral-500"
        >
          Stan backendu
        </h2>

        <div className="mt-4">
          <BackendStatus
            isPending={health.isPending}
            isError={health.isError}
            data={health.data}
          />
        </div>
      </section>
    </main>
  );
}

type HealthPayload = {
  data?: { status?: string; services?: Record<string, string> };
};

function BackendStatus({
  isPending,
  isError,
  data,
}: {
  isPending: boolean;
  isError: boolean;
  data: unknown;
}) {
  if (isPending) {
    return <p className="text-base text-neutral-500">Sprawdzanie…</p>;
  }

  if (isError) {
    return (
      <p role="status" className="text-base text-danger-700">
        Backend nie odpowiada. Uruchom go poleceniem{" "}
        <code className="font-mono text-sm">task backend:run</code>.
      </p>
    );
  }

  const payload = (data as HealthPayload | undefined)?.data;
  const services = payload?.services ?? {};

  return (
    <div className="flex flex-col gap-3">
      <p role="status" className="text-base text-success-700">
        Backend odpowiada: {payload?.status ?? "brak statusu"}
      </p>

      {Object.keys(services).length > 0 && (
        <dl className="grid grid-cols-2 gap-x-6 gap-y-1">
          {Object.entries(services).map(([name, state]) => (
            <div key={name} className="contents">
              <dt className="text-sm text-neutral-500">{name}</dt>
              <dd className="text-sm text-neutral-800">{state}</dd>
            </div>
          ))}
        </dl>
      )}
    </div>
  );
}
