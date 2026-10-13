# SeaweedFS zamiast MinIO; S3 neutralne wobec dostawcy

MinIO nie ma już wsparcia, więc magazynem S3 we wszystkich środowiskach
(dev, test, prod na VPS) jest SeaweedFS 4.48 (Apache 2.0, obraz
`chrislusf/seaweedfs:4.48`): jeden proces `weed server` (master + volume +
filer + bramka S3 na 8333) plus `weed admin` jako UI (dev: port
`S3_CONSOLE_PORT`, prod: tylko `127.0.0.1` pod tunel SSH). Danych w MinIO nie
było — jedyny stan to buckety zakładane przy starcie przez `sync_buckets()`,
którego logika się nie zmienia.

Kod aplikacji nie zna nazwy dostawcy (cel: uniwersalne S3). Zmiana dostawcy
to wyłącznie zmiana obrazu w compose, portów i credentiali: flaga `USE_S3`
mówi tylko „S3 albo dysk", kształt adresu biorą generyczne `AWS_S3_*` i
`S3_PUBLIC_BASE_URL`, a credentiale serwera generują przy starcie
`/etc/seaweedfs/s3.json` (`-s3.config`). Brak credentiali zatrzymuje start
z czytelnym błędem, zamiast serwować otwarty magazyn.

Odrzucone: Floci (emulator, nie magazyn produkcyjny) i Garage (brak bucket
policy — wymagałby kroku specyficznego dla dostawcy, wbrew neutralności).

## Consequences

Zamiana dostawcy nie rusza kodu aplikacji ani testów polityk
(`test_storage_policies.py` przechodzi bez zmian w asercjach): egzekwowanie
`PutBucketPolicy`, wygasanie podpisu SigV4 i 403 na zły klucz zweryfikowane
na SeaweedFS 4.48 tak samo jak wcześniej.
