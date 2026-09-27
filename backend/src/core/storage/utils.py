import sys
from dataclasses import dataclass, field

from core.storage.bucket_manager import S3BucketManager
from core.storage.buckets import ALL_BUCKETS, Bucket


@dataclass
class SyncResult:
    success: bool
    created: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def exit_on_failure(self) -> None:
        """Zakończ proces z kodem 1 jeśli synchronizacja nie powiodła się."""
        if not self.success:
            for error in self.errors:
                print(f"❌ {error}", file=sys.stderr)
            sys.exit(1)


def sync_buckets(buckets: tuple[Bucket, ...] = ALL_BUCKETS) -> SyncResult:
    """Zakłada buckety z ADR 0025 i nakłada na nie polityki dostępu.

    Nie kasuje niczego, czego nie ma na liście — wcześniejsza wersja to
    robiła, a bootstrap uruchamiany przy starcie kontenera nie jest miejscem,
    w którym kasuje się magazyn. Usunięcie bucketa zostaje czynnością świadomą.

    Polityka jest nakładana także na bucket, który już istniał: inaczej
    `products` założony ręcznie zostałby prywatny i zdjęcia nie wyświetliłyby
    się nikomu.
    """
    result = SyncResult(success=True)

    try:
        manager = S3BucketManager()
    except Exception as exc:
        result.success = False
        result.errors.append(f"Nie udało się połączyć z S3: {exc}")
        return result

    for bucket in buckets:
        try:
            if manager.ensure(bucket):
                result.created.append(bucket.name)
            else:
                result.updated.append(bucket.name)
        except Exception as exc:
            result.success = False
            result.errors.append(
                f"Nie udało się przygotować bucketu '{bucket.name}': {exc}"
            )

    return result
