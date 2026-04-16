import os
import sys
from dataclasses import dataclass, field

from .bucket_manager import S3BucketManager


@dataclass
class SyncResult:
    success: bool
    created: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def exit_on_failure(self) -> None:
        """Zakończ proces z kodem 1 jeśli synchronizacja nie powiodła się."""
        if not self.success:
            for error in self.errors:
                print(f"❌ {error}", file=sys.stderr)
            sys.exit(1)


def get_buckets_names_from_env() -> list[str]:
    """
    Pobierz listę nazw bucketów ze zmiennej środowiskowej S3_BUCKETS_NAMES.

    Zmienna powinna być listą nazw oddzieloną przecinkami, np.:
        S3_BUCKETS_NAMES=static,public,products

    Returns:
        list[str]: Lista nazw bucketów.
    """
    raw_value = os.getenv("S3_BUCKETS_NAMES", "")
    return [name.strip() for name in raw_value.split(",") if name.strip()]


def sync_buckets(buckets_names: str) -> SyncResult:
    """
    Synchronizuj buckety S3/MinIO z przekazaną listą nazw.

    Args:
        buckets_names (str): Nazwy bucketów oddzielone przecinkami, np. "static,public,products".
                             Wartość powinna pochodzić z zewnątrz (np. ze zmiennej S3_BUCKETS_NAMES).

    Logika:
    - Jeśli bucket z listy istnieje → nic nie robi.
    - Jeśli bucket z listy nie istnieje → tworzy go.
    - Jeśli bucket istnieje w S3, ale nie ma go na liście → kasuje go.

    Returns:
        SyncResult: Wynik synchronizacji z listami utworzonych/usuniętych bucketów i ewentualnymi błędami.
    """
    result = SyncResult(success=True)

    try:
        manager = S3BucketManager()
        expected_buckets = set(
            name.strip() for name in buckets_names.split(",") if name.strip()
        )
        existing_buckets = set(manager.list_buckets())
    except Exception as exc:
        result.success = False
        result.errors.append(f"Nie udało się połączyć z S3: {exc}")
        return result

    # Utwórz brakujące buckety
    for bucket_name in expected_buckets - existing_buckets:
        try:
            manager.create_bucket(bucket_name)
            result.created.append(bucket_name)
        except Exception as exc:
            result.success = False
            result.errors.append(f"Nie udało się utworzyć bucketu '{bucket_name}': {exc}")

    # Usuń buckety których nie ma na liście
    for bucket_name in existing_buckets - expected_buckets:
        try:
            manager.delete_bucket(bucket_name)
            result.deleted.append(bucket_name)
        except Exception as exc:
            result.success = False
            result.errors.append(f"Nie udało się usunąć bucketu '{bucket_name}': {exc}")

    return result
