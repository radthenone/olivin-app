import { Skeleton } from "@/components/ui/skeleton";

/**
 * Szkielet siatki produktów używany w `loading.tsx` i w Suspense fallbackach.
 */
export function ProductGridSkeleton({ count = 8 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {Array.from({ length: count }).map((_, index) => (
        <div
          className="flex flex-col gap-3 rounded-xl border border-neutral-200 bg-neutral-0 p-4"
          key={index}
        >
          <Skeleton className="aspect-square w-full rounded-lg" />
          <Skeleton className="h-5 w-3/4 rounded-md" />
          <Skeleton className="h-4 w-1/3 rounded-md" />
        </div>
      ))}
    </div>
  );
}

/**
 * Szkielet całej strony katalogu (nawigacja + nagłówek + siatka).
 */
export function CatalogPageSkeleton() {
  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-8 px-6 py-8">
      <div className="flex flex-col gap-2">
        <Skeleton className="h-9 w-64 rounded-md" />
        <Skeleton className="h-5 w-96 rounded-md" />
      </div>

      <div className="grid grid-cols-1 gap-8 md:grid-cols-4">
        <aside className="md:col-span-1">
          <div className="flex flex-col gap-3 rounded-xl border border-neutral-200 bg-neutral-0 p-4">
            <Skeleton className="h-4 w-28 rounded-md" />
            <Skeleton className="h-4 w-full rounded-md" />
            <Skeleton className="h-4 w-3/4 rounded-md" />
            <Skeleton className="h-4 w-5/6 rounded-md" />
          </div>
        </aside>

        <section className="md:col-span-3">
          <ProductGridSkeleton count={6} />
        </section>
      </div>
    </div>
  );
}
