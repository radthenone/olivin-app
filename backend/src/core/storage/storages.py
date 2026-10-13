"""Klasy magazynu — po jednej na bucket z ADR 0025.

Model trzyma wyłącznie klucz obiektu: bez hosta i bez nazwy bucketa. Adres
składa warstwa serializacji, bo host zmienia się razem ze środowiskiem
(lokalny S3 w dev, inny adres w produkcji), a klucz zapisany razem z hostem
trzeba by migrować przy każdej takiej zmianie.

Kształt adresu zależy wyłącznie od generycznych ustawień S3
(`AWS_S3_ADDRESSING_STYLE`, `AWS_S3_URL_PROTOCOL`, `AWS_S3_CUSTOM_DOMAIN`,
`S3_PUBLIC_BASE_URL`) — kod nie zgaduje dostawcy po nazwie hosta.
"""

from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

from core.storage.buckets import DOCUMENTS, ORIGINALS, PRODUCTS, Bucket


class BucketStorage(S3Boto3Storage):
    """Magazyn związany z jednym bucketem i jego polityką.

    Atrybut nazywa się `bucket_spec`, a nie `bucket`: `S3Boto3Storage` ma
    własne `bucket` — zasób boto3, przez który idzie każdy zapis i odczyt.
    Przesłonięcie go wywraca całe wejście-wyjście magazynu.
    """

    bucket_spec: Bucket

    @classmethod
    def _get_endpoint_url(cls) -> str | None:
        """Adres dostawcy. `None` oznacza właściwy AWS, nie brak konfiguracji.

        Tylko z ustawień Django — bez czytania `os.environ`. Ustawienia
        testowe są hermetyczne, a pola plików wiążą magazyn przy imporcie
        modeli, czyli zanim jakikolwiek fixture zdążyłby env posprzątać.
        """
        return getattr(settings, "AWS_S3_ENDPOINT_URL", None) or None

    @classmethod
    def _get_url_protocol(cls) -> str:
        """`http:` albo `https:` — schemat dokładany przed adres publiczny."""
        return getattr(settings, "AWS_S3_URL_PROTOCOL", None) or "http:"

    @classmethod
    def _get_addressing_style(cls) -> str:
        """`path` dokleja bucket do ścieżki, `virtual` wstawia go w host."""
        return getattr(settings, "AWS_S3_ADDRESSING_STYLE", None) or "path"

    @classmethod
    def _get_custom_domain(cls) -> str:
        """Własna domena bez schematu i bez końcowego ukośnika."""
        return (getattr(settings, "AWS_S3_CUSTOM_DOMAIN", None) or "").rstrip("/")

    @classmethod
    def _get_public_base(cls) -> tuple[str, str]:
        """Baza publicznych adresów jako para (protokół, host-z-prefiksem).

        `S3_PUBLIC_BASE_URL` wygrywa i może nieść prefiks ścieżki (np. adres
        spod reverse proxy). django-storages dokleja protokół samo, więc
        schemat jest zwracany osobno, a prefiks zostaje w hoście.
        """
        base = (getattr(settings, "S3_PUBLIC_BASE_URL", None) or "").strip().rstrip("/")
        if base:
            if base.startswith("https://"):
                return "https:", base[len("https://") :]
            if base.startswith("http://"):
                return "http:", base[len("http://") :]
            return cls._get_url_protocol(), base
        domain = cls._get_custom_domain()
        if domain:
            return cls._get_url_protocol(), domain
        endpoint = (cls._get_endpoint_url() or "").rstrip("/")
        for scheme in ("https://", "http://"):
            if endpoint.startswith(scheme):
                return cls._get_url_protocol(), endpoint[len(scheme) :]
        if endpoint:
            return cls._get_url_protocol(), endpoint
        return cls._get_url_protocol(), "localhost"

    def __init__(self, **kwargs):
        self.bucket_name = self.bucket_spec.name
        self.endpoint_url = self._get_endpoint_url()
        if self.bucket_spec.is_public:
            bucket = self.bucket_spec.name.strip("/")
            protocol, host = self._get_public_base()
            self.url_protocol = protocol
            # Prefiks ścieżki nie składa się z subdomeną — wtedy wygrywa
            # zwykły adres ze ścieżką, tak samo jak przy reverse proxy.
            if self._get_addressing_style() == "virtual" and "/" not in host:
                self.custom_domain = f"{bucket}.{host}"
            else:
                self.custom_domain = f"{host}/{bucket}"
        else:
            # Prywatny bucket nie może mieć własnej domeny: django-storages
            # zwraca wtedy gotowy adres i **pomija podpisywanie**, czyli
            # `documents` przestałoby być prywatne w jedyny sposób, w jaki
            # o tym wiemy — przez adres, który nie działa bez podpisu.
            # Podpis idzie przez host endpointu bez prefiksu ścieżki, bo
            # prefiks unieważnia podpis SigV4.
            self.custom_domain = None
        super().__init__(**kwargs)


class ProductStorage(BucketStorage):
    """Zdjęcia katalogu — odczyt publiczny, adres bez podpisu."""

    bucket_spec = PRODUCTS
    location = ""
    default_acl = None
    file_overwrite = True
    querystring_auth = False


class OriginalStorage(BucketStorage):
    """Oryginały zdjęć — prywatne, czytane wyłącznie przez zadania w tle."""

    bucket_spec = ORIGINALS
    location = ""
    default_acl = None
    file_overwrite = False
    querystring_auth = True


class DocumentStorage(BucketStorage):
    """Dokumenty sprzedaży i certyfikaty — prywatne, adres podpisany na czas."""

    bucket_spec = DOCUMENTS
    location = ""
    default_acl = None
    file_overwrite = False
    querystring_auth = True


_BY_BUCKET: dict[str, type[BucketStorage]] = {
    PRODUCTS.name: ProductStorage,
    ORIGINALS.name: OriginalStorage,
    DOCUMENTS.name: DocumentStorage,
}


def storage_for(bucket: Bucket) -> BucketStorage:
    """Magazyn obsługujący dany bucket.

    Pozwala warstwie serializacji poprosić o adres, podając bucket z ADR 0025,
    bez wiedzy o tym, która klasa go obsługuje.
    """
    try:
        return _BY_BUCKET[bucket.name]()
    except KeyError:
        raise ValueError(f"Nie ma magazynu dla bucketa {bucket.name}") from None
