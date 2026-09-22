# Graph Report - backend  (2026-09-22)

## Corpus Check
- 282 files · ~59,741 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 3, .lock 1)

## Summary
- 2211 nodes · 4784 edges · 193 communities (105 shown, 88 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 336 edges (avg confidence: 0.95)
- Token cost: 94,912 input · 0 output

## Community Hubs (Navigation)
- OpenAPI Schema Contract
- Collections Tests
- Allauth Mail Adapter
- Product Model & Admin
- Test Fixtures & Health
- Account Model Tests
- Product Views Tests
- Money Fields & Slugs
- Django App Configs
- Gemstone Tests
- Storage Policies & Buckets
- Product Choices & Gemstone
- Account Service Tests
- Address & Profile Views
- Accounts Migrations
- Storage Tests
- Category Model Tests
- Money Value Object
- Env & ASGI Setup
- API Conventions Tests A
- Profile Serializers
- Account View Tests
- Product & Core Serializers
- Category View Tests
- Product Model Tests A
- Profile Model & Service
- Translation Service & Models
- Metal Rate Admin
- Consent View Tests
- API Filters & Conventions
- Translation Warnings Tests
- Metal Rate Pricing Tests
- Pricing Engine Tests
- Category Model & Admin
- Product Model Tests B
- Product Image Tests A
- Translated Serializers
- Consent Serializers & Views
- Translation Admin
- Money Tests
- Auth & Health Views
- Inventory Model Tests
- Product & CSRF Views
- Inventory Tests B
- DeepL Translation Adapter
- Category Serializers & i18n Schema
- Collection Model & Admin
- Translation Tasks
- Storage Utils
- Metal Rate Providers
- Image Processing
- Product Variant Model
- Translation Service Tests
- Inventory Tests C
- Product Filter Tests A
- Document Storage Backends
- Consent Model Tests A
- Inventory Model & Admin
- Stock in Product View
- Image Pipeline Tests
- Pricing Rules Tests
- Translation Fallback Tests
- Money Allocation
- Consent Models
- Product Image Model
- Account Test Fixtures
- Storage Tests B
- Product Filter Tests B
- Product Filter Tests C
- Language Resolution
- Shared Admin Config
- Consent Admin
- Inventory Admin
- Product Search
- VAT Calculation
- Settings Components
- Bucket Manager
- Consent Model Tests B
- Product Filter Tests D
- Image Tests B
- Allauth Selectors & Tasks
- Category Views
- Translation Admin Tests
- Repricing Tasks
- Storage URLs
- Image Tests C
- Inventory Tests D
- Slug Utilities
- Product Filter Tests E
- Gemstone Model
- Image Model Tests
- Product Celery Tasks
- Category Model Tests B
- Product Model Tests C
- Translation Test Helpers
- Consent Model Core
- Consent Model Tests C
- API Conventions Tests B
- Celery Bootstrap
- API Conventions Tests C
- Integration Fixtures
- Image Tests D
- Catalog Factories
- Product View Helpers
- Consent Model Helpers
- Cost Component Model
- Pricing Rounding Tests
- Testing Settings
- API Conventions Tests D
- Storage Tests C
- Product Filter Tests F
- LibreTranslate Adapter
- Translation Tests Misc
- Celery Schedules
- MetalRate QuerySet
- Translation QuerySet
- Filter Test Catalog
- Fake Translation Provider
- Integrations Package
- Stub: pyproject.toml
- Stub: README.md

## God Nodes (most connected - your core abstractions)
1. `PublishedProductFactory` - 137 edges
2. `Money` - 101 edges
3. `CategoryFactory` - 100 edges
4. `ProductVariantFactory` - 88 edges
5. `ProductFactory` - 56 edges
6. `ProfileFactory` - 51 edges
7. `ProductVariant` - 44 edges
8. `UserFactory` - 43 edges
9. `CollectionFactory` - 43 edges
10. `Category` - 40 edges

## Surprising Connections (you probably didn't know these)
- `CustomUserAdmin` --uses--> `CustomUser`  [INFERRED]
  src/apps/accounts/admin.py → src/apps/accounts/models/user_model.py
- `Profile` --uses--> `RoleChoices`  [INFERRED]
  src/apps/accounts/models/profile_model.py → src/apps/accounts/models/roles_model.py
- `ProfileFactory` --uses--> `RoleChoices`  [INFERRED]
  src/tests/factories/accounts.py → src/apps/accounts/models/roles_model.py
- `Category` --uses--> `Money`  [INFERRED]
  src/apps/categories/models.py → src/common/money/money.py
- `Category` --uses--> `SlugSourceUnavailable`  [INFERRED]
  src/apps/categories/models.py → src/common/slugs.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Public catalog read API (categories, collections, products)** — src_schema_categories_list, src_schema_categories_retrieve, src_schema_collections_list, src_schema_collections_retrieve, src_schema_products_list, src_schema_products_retrieve [INFERRED 0.85]
- **Versioned consent flow** — src_schema_consents_documents_list, src_schema_consents_create, src_schema_consent, src_schema_consentdocument, src_schema_consentkindenum [EXTRACTED 1.00]
- **Product/variant pricing and tax model** — src_schema_productvariant, src_schema_money, src_schema_adr_0009, src_schema_adr_0013, src_schema_adr_0022 [INFERRED 0.85]

## Communities (193 total, 88 thin omitted)

### Community 0 - "OpenAPI Schema Contract"
Cohesion: 0.07
Nodes (59): Address, ADR 0009 (Money as integer minor units), ADR 0013 (VAT exemption for investment gold), ADR 0018 (Engraving), ADR 0022 (Manual price precedence), ADR 0024 (Made-to-order products), ADR 0025 (Object storage keys / private buckets), BlankEnum (+51 more)

### Community 1 - "Collections Tests"
Cohesion: 0.08
Nodes (27): django_db_utils, post_generation, django_db, Slug jest angielskim adresem kampanii — jeden, unikalny, niezmienny., Kolekcja przecina kategorie; produkt należy do wielu kolekcji., TestMembership, TestSlug, _collection_names() (+19 more)

### Community 2 - "Allauth Mail Adapter"
Cohesion: 0.06
Nodes (36): allauth_account_adapter, DefaultAccountAdapter, django_core_mail, django_db_transaction, django_forms, EmailMultiAlternatives, json, AsyncAccountAdapter (+28 more)

### Community 3 - "Product Model & Admin"
Cohesion: 0.06
Nodes (26): Any, Identyfikatory kategorii o podanym slugu wraz ze wszystkimi potomkami. Klient…, MetalRateAdmin, ProductAdmin, ProductVariantAdmin, action, display, HttpRequest (+18 more)

### Community 4 - "Test Fixtures & Health"
Cohesion: 0.05
Nodes (39): AbstractBaseUser, BaseUserManager, DefaultSocialAccountAdapter, django_contrib_auth_models, django_core_cache, fakeredis, moto, patch (+31 more)

### Community 5 - "Account Model Tests"
Cohesion: 0.05
Nodes (29): django_db, Dwóch użytkowników z tym samym username powinno rzucić IntegrityError., Użytkownik z is_active=False powinien być poprawnie tworzony., USERNAME_FIELD powinien wskazywać na 'email'., REQUIRED_FIELDS poza emailem powinno być puste., Testy CustomUserManager — create_user i create_superuser., create_user bez emaila powinien rzucić ValueError., Email powinien być znormalizowany (małe litery domeny). (+21 more)

### Community 6 - "Product Views Tests"
Cohesion: 0.11
Nodes (26): EngravableProductFactory, PublishedProductFactory, Sygnet: opublikowany, z grawerem wycenionym osobno (ADR 0018)., _detail(), _get(), Any, APIClient, django_db (+18 more)

### Community 7 - "Money Fields & Slugs"
Cohesion: 0.09
Nodes (25): django_conf, django_contrib_contenttypes_fields, django_core_exceptions, Model, re, RuntimeError, ProductImageQuerySet, Meta (+17 more)

### Community 8 - "Django App Configs"
Cohesion: 0.05
Nodes (27): django_apps, AccountsConfig, AppConfig, CategoriesConfig, AppConfig, CollectionsConfig, AppConfig, ConsentsConfig (+19 more)

### Community 9 - "Gemstone Tests"
Cohesion: 0.10
Nodes (18): validate_certificate(), GemstoneFactory, Fabryka kamienia. Certyfikat dokłada się osobno — bywa, że go nie ma., certificate_file(), Any, ContentFile, django_db, Kamienie na wariancie i certyfikaty laboratorium. (+10 more)

### Community 10 - "Storage Policies & Buckets"
Cohesion: 0.09
Nodes (23): Config, Polityka bucketu albo `None`, gdy żadnej nie ma., Usuń bucket z dostawcy magazynu S3. Args: bucket_name (str): Nazwa bucketu do…, Zwróć listę wszystkich bucketów w dostawcy magazynu S3. Returns: list: Lista…, S3BucketManager, _fetch(), key(), manager() (+15 more)

### Community 11 - "Product Choices & Gemstone"
Cohesion: 0.13
Nodes (27): decimal, django_filters, Fineness, Length, Material, MetalColor, ProductStatus, Zamknięte listy wartości cech katalogu. Cechy produktu i wariantu są wyborem z… (+19 more)

### Community 12 - "Account Service Tests"
Cohesion: 0.07
Nodes (21): freeze_time, full_name powinien zwracać 'Imię Nazwisko'., full_name bez last_name powinien zwrócić samo imię., full_name bez first_name powinien zwrócić samo nazwisko., full_name gdy oba pola puste powinien zwrócić pusty string., Testy właściwości age modelu Profile., age powinien wynosić None gdy date_of_birth jest None., age powinien poprawnie obliczać wiek po urodzinach w danym roku. (+13 more)

### Community 13 - "Address & Profile Views"
Cohesion: 0.08
Nodes (19): address_schema, CountryFieldMixin, django_countries_serializers, phonenumber_field_serializerfields, profile_schema, rest_framework_decorators, rest_framework_exceptions, rest_framework_permissions (+11 more)

### Community 14 - "Accounts Migrations"
Cohesion: 0.10
Nodes (21): django_core_validators, django_countries_fields, django_db, django_db_models_deletion, django_db_models_functions_text, django_utils_timezone, phonenumber_field_modelfields, Migration (+13 more)

### Community 15 - "Storage Tests"
Cohesion: 0.10
Nodes (21): boto3, botocore_config, botocore_exceptions, enum, Adres do prywatnego obiektu, ważny przez zadany czas. Jedyna droga do bucketa…, Bucket, BucketAccess, public_read_policy() (+13 more)

### Community 16 - "Category Model Tests"
Cohesion: 0.10
Nodes (12): Drzewo jest listą sąsiedztwa: rodzic opcjonalny, potomkowie przez relację., `save()` nie woła `clean()`, a pętla to uszkodzenie danych: gałąź bez korzenia…, Slug jest angielskim adresem kategorii — jeden, unikalny, niezmienny., Nie z nazwy polskiej pozbawionej ogonków — adres ma być angielski…, Cichy odwrót do nazwy polskiej byłby dokładnie tym błędem, który ta warstwa ma…, Jedyna droga niezależna od sieci — i dlatego ma pierwszeństwo., TestSlug, TestTree (+4 more)

### Community 17 - "Money Value Object"
Cohesion: 0.10
Nodes (7): Cena wyliczona ze wzoru, bez względu na cenę ręczną., Cena, którą widzi klient — ręczna ma pierwszeństwo (ADR 0022)., components_total(), Money, Mnożenie przez liczbę sztuk. Ułamek — `multiply`, żeby zaokrąglenie było jawne., Kwota jako liczba całkowita groszy plus kod waluty. Niezmienna wartość, nie…, TestMoneyArithmetic

### Community 18 - "Env & ASGI Setup"
Cohesion: 0.08
Nodes (16): corsheaders_defaults, django_core_asgi, django_core_wsgi, os, pathlib, split_settings_tools, ASGI config for core project. It exposes the ASGI callable as a module-level…, load_valid_envs() (+8 more)

### Community 19 - "API Conventions Tests A"
Cohesion: 0.11
Nodes (21): factory_faker, freezegun, pytest, rest_framework_response, rest_framework_test, rest_framework_throttling, RoleChoices, Components package for Django settings. (+13 more)

### Community 20 - "Profile Serializers"
Cohesion: 0.09
Nodes (19): Meta, ProfileSerializer, date, Waliduje, że klient ma ukończone 18 lat., date, django_db, Data urodzenia osoby pełnoletniej powinna przejść walidację., Zwraca datę przesuniętą o liczbę lat z obsługą 29 lutego. (+11 more)

### Community 21 - "Account View Tests"
Cohesion: 0.08
Nodes (20): APIClient, django_db, PATCH cudzego profilu powinien zwrócić 404., PATCH change-role powinien przełączać rolę z CUSTOMER na ADMIN., PATCH change-role powinien przełączać rolę z ADMIN na CUSTOMER., Testy autoryzacji ProfileViewSet., GET list profili bez tokenu powinien zwrócić 403 (lub 401)., GET list profili z tokenem powinien zwrócić 200. (+12 more)

### Community 22 - "Product & Core Serializers"
Cohesion: 0.12
Nodes (20): django_utils_translation, extend_schema_field, rest_framework_filters, rest_framework_settings, GemstoneSerializer, Meta, ProductDetailSerializer, ProductImageSerializer (+12 more)

### Community 23 - "Category View Tests"
Cohesion: 0.13
Nodes (14): _by_name(), _names(), Any, APIClient, django_db, parametrize, Zapis pętli nie przepuszcza, ale `UPDATE` z pominięciem modelu już tak., Taksonomię układa panel, nie API (ADR 0021). (+6 more)

### Community 24 - "Product Model Tests A"
Cohesion: 0.10
Nodes (12): ProductFactory, Fabryka dla modelu Product — domyślnie szkic, jak po założeniu w panelu., django_db, Produkt należy do kategorii-liścia (`CONTEXT.md`, Category)., Produkt na zamówienie ma czas realizacji; magazynowy go nie ma (ADR 0024)., Slug produktu zamraża się przy publikacji, nie przy pierwszym zapisie., Adres powstaje przy publikacji (`.ai/project.md`) — szkic nie ma go pod czym…, Kolumna sluga jest unikalna, więc pusty adres musi być `NULL`, a nie pustym… (+4 more)

### Community 25 - "Profile Model & Service"
Cohesion: 0.10
Nodes (19): allauth_account_forms, allauth_account_internal_emailkit, allauth_account_utils, allauth_socialaccount_adapter, allauth_socialaccount_models, SignupForm, Meta, Profile (+11 more)

### Community 26 - "Translation Service & Models"
Cohesion: 0.15
Nodes (19): collections_abc, django_contrib_contenttypes_admin, django_contrib_contenttypes_forms, django_contrib_contenttypes_models, django_utils, Język treści wybrany przez klienta., Language, Języki treści katalogu. Polski jest źródłem — nie ma dla niego wpisów w tej… (+11 more)

### Community 27 - "Metal Rate Admin"
Cohesion: 0.10
Nodes (19): dataclasses, CostComponentInline, GemstoneInline, ProductImageInline, ProductVariantInline, Kamienie przy wariancie — parametry i certyfikat w jednym miejscu., Składniki kosztu przy wariancie — lista otwarta (ADR 0022)., Warianty edytowane przy produkcie — osobny ekran rozbiłby jedną pracę. (+11 more)

### Community 28 - "Consent View Tests"
Cohesion: 0.17
Nodes (15): _consents_url(), _documents_url(), APIClient, django_db, Testy API zgód na realnym kształcie odpowiedzi (`response.json()`, camelCase)., Podmiot jest dokładnie jeden — e-mail przy koncie to niejasność, nie wygoda., Klient pokazał starą wersję — musi odświeżyć listę, nie zapisać zgody, która i…, Zgody nie są zasobem do przeglądania przez API — panel je widzi. (+7 more)

### Community 29 - "API Filters & Conventions"
Cohesion: 0.10
Nodes (12): PageNumberPagination, rest_framework_pagination, `SearchFilter`, który nie ogłasza parametru, którego widok nie obsługuje.…, SearchFilter, Konwencje warstwy API wspólne dla wszystkich aplikacji domenowych. Paginacja,…, Paginacja numerowana wspólna dla całego API. Dwadzieścia cztery pozycje na…, StandardPagination, _page_size_for() (+4 more)

### Community 30 - "Translation Warnings Tests"
Cohesion: 0.11
Nodes (13): Pola zmienione w tym zapisie, które mają poprawione ręcznie tłumaczenie.…, stale_manual_fields(), add_translation(), django_db, Uzupełnianie brakujących tłumaczeń., Adres powstaje z nazwy angielskiej, więc publikacja tłumaczy ją od razu —…, Właściciel poprawia tłumaczenie, bo automat się pomylił., Zmiana tekstu polskiego przy poprawce ręcznej wymaga ostrzeżenia. (+5 more)

### Community 31 - "Metal Rate Pricing Tests"
Cohesion: 0.18
Nodes (14): django_core, activate_rate(), Zatwierdza kurs: archiwizuje poprzedni, kolejkuje przeliczenie i e-mail. Trzy…, MetalRateFactory, Fabryka dla modelu MetalRate — domyślnie kurs zaproponowany. Aktywny kurs…, active_gold_rate(), on_commit(), fixture (+6 more)

### Community 32 - "Pricing Engine Tests"
Cohesion: 0.16
Nodes (11): active_rate_for(), calculate_price(), cost_floor(), Cena wyliczona ze wzoru albo `None`, gdy brak aktywnego kursu., Koszt wariantu bez marży (`CONTEXT.md`, Cost floor). `None`, gdy nie ma…, Cena ręczna nie schodzi poniżej kosztu bez marży (ADR 0022)., Wariant zakładany przed ustaleniem kursu nie może się o to rozbić., cena = (masa × kurs + składniki) × marża, zaokrąglone w górę. (+3 more)

### Community 33 - "Category Model & Admin"
Cohesion: 0.13
Nodes (11): CategoryAdmin, display, HttpRequest, QuerySet, register, Panel taksonomii — jedyne miejsce, w którym drzewo się zmienia (ADR 0021)., Category, Meta (+3 more)

### Community 34 - "Product Model Tests B"
Cohesion: 0.13
Nodes (11): Params, ProductVariantFactory, Fabryka dla modelu ProductVariant — domyślnie ze stawką podatku. Zwolnienie…, Any, parametrize, Cena jest w kolumnie; ręczna ma pierwszeństwo (ADR 0009, ADR 0022)., Adnotacja, bo po tej wartości idzie sortowanie i wybór najtańszego., Walidatory pól działają tylko w `full_clean()` — zapis programowy (import,… (+3 more)

### Community 35 - "Product Image Tests A"
Cohesion: 0.15
Nodes (10): add_image(), on_commit(), fixture, Image, Zadanie tnie oryginał i zapisuje trzy rozmiary WebP., Zmiana kadru uruchamia to samo zadanie na zachowanym oryginale., Uruchamia zadanie odłożone na po zatwierdzeniu transakcji., read_rendition() (+2 more)

### Community 36 - "Translated Serializers"
Cohesion: 0.13
Nodes (13): collection_schema, rest_framework, rest_framework_views, CollectionSerializer, Meta, Kolekcja na liście — bez produktów, z ich liczbą. Lista kolekcji służy do…, CollectionViewSet, QuerySet (+5 more)

### Community 37 - "Consent Serializers & Views"
Cohesion: 0.16
Nodes (14): consent_document_schema, consent_schema, ConsentDocument, Meta, Wersja regulaminu, polityki prywatności albo zgody marketingowej. Wersjonowanie…, ConsentDocumentSerializer, ConsentSerializer, Meta (+6 more)

### Community 38 - "Translation Admin"
Cohesion: 0.15
Nodes (12): BaseGenericInlineFormSet, action, HttpRequest, QuerySet, register, Zapis tłumaczenia z panelu to zawsze poprawka człowieka. Znakowanie siedzi w…, Przegląd tłumaczeń katalogu., TranslationAdmin (+4 more)

### Community 39 - "Money Tests"
Cohesion: 0.12
Nodes (6): minor_digits(), Decimal, Buduje kwotę z wartości w jednostce głównej (np. `"19.99"`). Przyjmuje str i…, Wartość w jednostce głównej, z dokładną liczbą miejsc po przecinku., Mnoży przez ułamek i zaokrągla dokładnie raz., TestMoneyConstruction

### Community 40 - "Auth & Health Views"
Cohesion: 0.16
Nodes (11): allauth_headless_spec_views, APIView, debug_toolbar_toolbar, drf_spectacular_views, health_schema, OpenAPIHTMLView, URL configuration for core project. The `urlpatterns` list routes URLs to…, AllauthRedocView (+3 more)

### Community 41 - "Inventory Model Tests"
Cohesion: 0.13
Nodes (11): Przyczyna ruchu. Stan bez przyczyny jest nie do rozliczenia., StockMovementReason, Wariant ze stanem: jeden ruch przyjęcia i ewentualna rezerwacja., stock(), django_db, parametrize, Stan magazynowy i dostępność widoczna na wariancie., Magazyn prowadzi panel — API go nie wystawia (ADR 0021). (+3 more)

### Community 42 - "Product & CSRF Views"
Cohesion: 0.15
Nodes (9): django_middleware_csrf, django_urls, extend_schema_view, product_schema, rest_framework_routers, Widoki aplikacji products — układ pakietowy, jak w apps.accounts., ProductViewSet, Katalog produktów dla sklepu. Actions: - list: GET /products/ — opublikowane,… (+1 more)

### Community 43 - "Inventory Tests B"
Cohesion: 0.22
Nodes (11): CostComponentFactory, InventoryItemFactory, Meta, DjangoModelFactory, Fabryka dla modelu CostComponent., Fabryka stanu magazynowego. Stan ustawia się ruchem, nie polem., Fabryka ruchu magazynowego., StockMovementFactory (+3 more)

### Community 44 - "DeepL Translation Adapter"
Cohesion: 0.17
Nodes (9): django_utils_module_loading, requests, Protocol, Silnik tłumaczenia treści katalogu (ADR 0027). Interfejs przyjmuje listę…, TranslationProvider, DeepLProvider, DeepL przez jego API tekstowe — dostawca produkcyjny (ADR 0027). Bez pakietu…, get_provider() (+1 more)

### Community 45 - "Category Serializers & i18n Schema"
Cohesion: 0.18
Nodes (10): drf_spectacular_utils, rest_framework_request, CategorySerializer, group_by_parent(), Meta, Any, Grupuje płaską listę węzłów po rodzicu. Drzewo składamy w pamięci z jednego…, Węzeł drzewa wraz z potomkami. Narzut nie wychodzi na zewnątrz: to dana… (+2 more)

### Community 46 - "Collection Model & Admin"
Cohesion: 0.15
Nodes (10): CollectionAdmin, display, HttpRequest, QuerySet, register, Panel kolekcji — jedyne miejsce, w którym powstają (ADR 0021)., Collection, Meta (+2 more)

### Community 47 - "Translation Tasks"
Cohesion: 0.15
Nodes (11): _published_only(), shared_task, Szkice są pomijane — tłumaczy się to, co klient może zobaczyć., Uzupełnia tłumaczenia jednego obiektu katalogu., Obchodzi opublikowany katalog i dokłada brakujące tłumaczenia. Zadanie okresowe…, translate_catalog_object(), translate_published_catalog(), Wyzwalacz drugi: obchód opublikowanego katalogu. (+3 more)

### Community 48 - "Storage Utils"
Cohesion: 0.14
Nodes (11): Zakończ proces z kodem 1 jeśli synchronizacja nie powiodła się., Zakłada buckety z ADR 0025 i nakłada na nie polityki dostępu. Nie kasuje…, sync_buckets(), SyncResult, main(), Django's command-line utility for administrative tasks., Run administrative tasks., Bootstrap zakłada buckety i nakłada polityki — i niczego nie kasuje. (+3 more)

### Community 49 - "Metal Rate Providers"
Cohesion: 0.23
Nodes (10): datetime, MetalQuote, MetalRateProvider, Protocol, Notowanie kruszcu przyniesione z zewnątrz. Nie jest modelem: dopóki właściciel…, Źródło notowań kruszców. Dostawca nie jest jeszcze wybrany (ADR 0027), więc…, LastActiveRateProvider, Dostawca zastępczy: powtarza ostatni zatwierdzony kurs. Dostawca notowań nie… (+2 more)

### Community 50 - "Image Processing"
Cohesion: 0.20
Nodes (12): django_core_files_base, io, pil, Przygotowanie zdjęć katalogu: kadr, skalowanie, WebP (ADR 0025)., `products/<id>/<uuid>-<rozmiar>.webp` — klucz bez hosta i bez bucketa., Zapisuje wszystkie rozmiary i oznacza zdjęcie jako gotowe., render_renditions(), rendition_key() (+4 more)

### Community 51 - "Product Variant Model"
Cohesion: 0.17
Nodes (7): Meta, ProductVariant, Ile sztuk klient może dziś kupić. `None` dla produktu na zamówienie: taki wyrób…, Produkt na zamówienie jest dostępny zawsze; magazynowy gdy ma stan., „Ostatnie sztuki" — stan dodatni, ale nie większy niż próg., Cena ręczna nie schodzi poniżej kosztu bez marży (ADR 0022). Sprawdzane w…, Kupowalny egzemplarz produktu (`CONTEXT.md`, ProductVariant). Wariant nosi…

### Community 52 - "Translation Service Tests"
Cohesion: 0.23
Nodes (7): Uzupełnia brakujące tłumaczenia obiektu. Nie rusza wpisów poprawionych ręcznie…, translate_object(), _get(), Any, API katalogu podaje pola w wybranym języku z odwrotem na polski., Świeżo opublikowany produkt ma być czytelny, zanim zadanie skończy. Opis, a nie…, TestCatalogApi

### Community 53 - "Inventory Tests C"
Cohesion: 0.17
Nodes (9): MadeToOrderProductFactory, Obrączki: wytwarzane po złożeniu zamówienia, z czasem realizacji., _detail(), Any, Produkt na zamówienie nie ma stanu i jest dostępny zawsze (ADR 0024)., Odwiedzający widzi dostępność na wariancie., Wariant bez stanu nie znika — jest widoczny jako niedostępny., TestAvailabilityInApi (+1 more)

### Community 54 - "Product Filter Tests A"
Cohesion: 0.19
Nodes (6): _names(), Any, Kategoria obejmuje swoje podkategorie — klient klika w węzeł, nie w liść., Wyszukiwarka po nazwie i opisie., TestCategoryFilter, TestSearch

### Community 55 - "Document Storage Backends"
Cohesion: 0.15
Nodes (12): S3Boto3Storage, documents_storage(), Magazyn dokumentów jako wywołanie, nie instancja zapisana w polu. Instancja…, originals_storage(), Magazyn oryginałów jako wywołanie, a nie instancja w polu. Instancja zapisana…, BucketStorage, DocumentStorage, OriginalStorage (+4 more)

### Community 56 - "Consent Model Tests A"
Cohesion: 0.23
Nodes (8): django_db_models_functions, ConsentKind, Gość nie ma konta — identyfikuje go e-mail podany w kasie., TestGuestConsent, GuestConsentFactory, Meta, DjangoModelFactory, Zgoda gościa — po e-mailu, bez konta. Osobna fabryka, nie podklasa…

### Community 57 - "Inventory Model & Admin"
Cohesion: 0.19
Nodes (8): InventoryItemAdmin, display, QuerySet, register, Magazyn prowadzony w panelu; API tylko pokazuje wynik (ADR 0021)., InventoryItem, Stan magazynowy wariantu (`CONTEXT.md`, InventoryItem). Wariant bez stanu nie…, Stan jako suma ruchów — nigdy pole nadpisywane.

### Community 58 - "Stock in Product View"
Cohesion: 0.15
Nodes (10): available_variants_subquery(), has_available_variant(), InventoryItemQuerySet, Meta, Warianty produktu, które klient może dziś kupić. Produkt na zamówienie jest…, Wyrażenie do adnotacji produktu: czy cokolwiek da się kupić., Dokłada stan liczony z ruchów oraz ilość faktycznie dostępną. Stan nie jest…, Pojedyncza zmiana stanu wraz z przyczyną (`CONTEXT.md`, StockMovement). Ilość… (+2 more)

### Community 59 - "Image Pipeline Tests"
Cohesion: 0.19
Nodes (9): apply_crop(), Image, Wycina prostokąt kadru; pusty kadr zostawia całe zdjęcie. Prostokąt jest…, Skaluje do zadanej szerokości, ale nigdy w górę. Powiększanie nie dokłada…, scale_to_width(), Kadr i skalowanie liczone bez bazy., Kadr przychodzi z klienta — nie ma powodu ufać, że się mieści., Powiększanie nie dokłada szczegółu, a waży swoje. (+1 more)

### Community 60 - "Pricing Rules Tests"
Cohesion: 0.18
Nodes (7): Margin, margin_for(), Narzut: procentowy albo kwotowy, nigdy oba naraz., Narzut wariantu, a w jego braku narzut kategorii produktu. Nadpisanie działa na…, Marża wariantu nadpisuje marżę kategorii., Nadpisanie działa na całym narzucie, nie na pojedynczym polu — złożenie dwóch…, TestMarginInheritance

### Community 61 - "Translation Fallback Tests"
Cohesion: 0.19
Nodes (7): Tekst w wybranym języku z odwrotem na polski. Fallback jest po to, żeby świeżo…, translated_value(), fake_provider(), on_commit(), fixture, Wyzwalacz pierwszy: przejście produktu na opublikowany., TestPublishTrigger

### Community 62 - "Money Allocation"
Cohesion: 0.22
Nodes (6): allocate(), Dzieli kwotę na `count` równych części; reszta na ostatnią., Dzieli kwotę proporcjonalnie do wag tak, żeby części sumowały się dokładnie do…, split_evenly(), parametrize, TestAllocate

### Community 63 - "Consent Models"
Cohesion: 0.21
Nodes (4): Consent, Zgoda klienta albo gościa na konkretną wersję dokumentu (`CONTEXT.md`,…, Zgoda należy do użytkownika albo do e-maila gościa — dokładnie jednego., TestSubjectIsUserXorEmail

### Community 64 - "Product Image Model"
Cohesion: 0.22
Nodes (5): Meta, ProductImage, Klucz oryginału w buckecie — bez hosta i bez nazwy bucketa., Nowe zdjęcie albo zmieniony kadr — w obu wypadkach to samo zadanie. Zmiana…, Zdjęcie produktu albo jego wariantu (`CONTEXT.md`, ProductImage). Oryginał…

### Community 65 - "Account Test Fixtures"
Cohesion: 0.21
Nodes (11): admin_factory(), profile_factory(), fixture, Fabryka użytkowników dostępna w testach accounts., Fabryka adminów dostępna w testach accounts., Fabryka profili dostępna w testach accounts., Użytkownik z powiązanym profilem., user_factory() (+3 more)

### Community 66 - "Storage Tests B"
Cohesion: 0.17
Nodes (6): django_db, parametrize, Przez magazyn da się zapisać i odczytać plik. Wygląda na oczywiste, a nie jest:…, Trzy buckety, podział po polityce dostępu, nie po rodzaju treści., TestBucketDefinitions, TestStorageReadsAndWrites

### Community 67 - "Product Filter Tests B"
Cohesion: 0.17
Nodes (3): Filtr po cesze wariantu idzie przez złączenie — bez `distinct` produkt z dwoma…, Każda cecha zawęża listę do produktów, które ją mają., TestFeatureFilters

### Community 68 - "Product Filter Tests C"
Cohesion: 0.17
Nodes (4): Sortowanie: cena rosnąco i malejąco, nowość, nazwa., Nazwy z samego ASCII, bo porządek liter spoza niego rozstrzyga collation bazy —…, Pusta cena — produkt bez wariantu — ląduje na końcu w obie strony, bo…, TestOrdering

### Community 69 - "Language Resolution"
Cohesion: 0.33
Nodes (5): language_from(), `?lang=` ma pierwszeństwo przed `Accept-Language`. Parametr w adresie jest…, FakeRequest, `?lang=` ma pierwszeństwo przed `Accept-Language`., TestLanguageResolution

### Community 70 - "Shared Admin Config"
Cohesion: 0.24
Nodes (7): django_contrib, django_contrib_auth_admin, django_db_models, django_http, CustomUserAdmin, register, UserAdmin

### Community 71 - "Consent Admin"
Cohesion: 0.22
Nodes (6): ConsentAdmin, ConsentDocumentAdmin, display, register, Rejestr zgód — do wglądu, nie do edycji: zgodę daje klient, nie panel., Nowa wersja dokumentu to nowy wpis, nie edycja starego (`CONTEXT.md`, Consent).

### Community 72 - "Inventory Admin"
Cohesion: 0.27
Nodes (5): HttpRequest, Dziennik ruchów — do przeglądania, nie do poprawiania., Ruchy przy stanie — jedyne miejsce, w którym stan się zmienia. Ruch zapisany…, StockMovementAdmin, StockMovementInline

### Community 73 - "Product Search"
Cohesion: 0.31
Nodes (7): QuerySet, Wyszukiwanie po nazwie i opisie produktu. Docelowym silnikiem jest…, Zawęża listę do produktów pasujących nazwą albo opisem., search(), _search_full_text(), _search_substring(), supports_full_text()

### Community 74 - "VAT Calculation"
Cohesion: 0.31
Nodes (4): Decimal, Wylicza netto i podatek z ceny brutto (Price w słowniku jest brutto). `rate` to…, split_gross(), TestSplitGross

### Community 75 - "Settings Components"
Cohesion: 0.20
Nodes (4): Django applications configuration., Authentication and authorization configuration., Django middleware configuration., Local development settings. Importuje development.py dla lokalnego developmentu.

### Community 76 - "Bucket Manager"
Cohesion: 0.22
Nodes (5): Utwórz bucket w dostawcy magazynu S3. Args: bucket_name (str): Nazwa bucketu do…, Upewnij się, że bucket istnieje w dostawcy magazynu S3. Jeśli nie istnieje,…, Nakłada na bucket politykę wynikającą z jego przeznaczenia (ADR 0025). Polityka…, Zakłada bucket, jeśli trzeba, i nakłada jego politykę. Returns: bool: True,…, Sprawdź, czy bucket istnieje w dostawcy magazynu S3. Args: bucket_name (str):…

### Community 77 - "Consent Model Tests B"
Cohesion: 0.31
Nodes (4): Nowa wersja dokumentu unieważnia wcześniejszą zgodę (`CONTEXT.md`, Consent)., TestConsentInvalidation, ConsentFactory, Zgoda zalogowanego klienta na dokument z fabryki.

### Community 78 - "Product Filter Tests D"
Cohesion: 0.20
Nodes (4): Cena liczy się po najtańszym wariancie produktu., Produkt z wariantem za 10 zł i za 3000 zł mieści się w progu 20 zł., Cena produktu to najtańszy wariant w ogóle, a nie najtańszy z tych, które…, TestPriceFilter

### Community 79 - "Image Tests B"
Cohesion: 0.22
Nodes (7): make_png(), Any, ContentFile, parametrize, Mała fixture: jednolity prostokąt, tani do zapisania i do policzenia., Kadr przychodzi z klienta, więc jest sprawdzany., TestCropValidation

### Community 80 - "Allauth Selectors & Tasks"
Cohesion: 0.28
Nodes (7): allauth_account_models, django_contrib_auth, pack_logger, get_stale_unverified_users_queryset(), QuerySet, cleanup_stale_unverified_users(), shared_task

### Community 81 - "Category Views"
Cohesion: 0.33
Nodes (6): category_schema, Request, Response, CategoryViewSet, Drzewo kategorii dla menu sklepu. Actions: - list: GET /categories/ — całe…, Całe drzewo jednym zapytaniem wraz z kontekstem serializera. `filter_queryset`…

### Community 82 - "Translation Admin Tests"
Cohesion: 0.28
Nodes (6): GenericTabularInline, Tłumaczenia przy obiekcie katalogu. Zapis z panelu oznacza wpis jako poprawiony…, TranslationInline, Zapis tłumaczenia z panelu oznacza je jako poprawione ręcznie. Znakowanie…, Zbiór formularzy taki, jaki panel buduje dla tego inline'u. Składany wprost, a…, TestAdminMarksManual

### Community 83 - "Repricing Tasks"
Cohesion: 0.28
Nodes (6): propose_metal_rates(), Raz w miesiącu wstawia notowania jako `proposed` (ADR 0022, ADR 0027).…, django_db, Zadanie okresowe wstawia propozycje, nie zmienia cen., Dostawca nie jest wybrany (ADR 0027), więc propozycja identyczna z obowiązującą…, TestProposeTask

### Community 84 - "Storage URLs"
Cohesion: 0.31
Nodes (5): object_url(), Adres obiektu: stały dla bucketa publicznego, podpisany dla prywatnego., Model trzyma sam klucz; adres składa warstwa serializacji., Klucz jest tym, co trzyma model — bez hosta i bez bucketa., TestObjectUrl

### Community 86 - "Inventory Tests D"
Cohesion: 0.31
Nodes (4): _names(), fixture, Produkt bez dostępnych wariantów trafia na koniec każdego sortowania., TestUnavailableProductsGoLast

### Community 87 - "Slug Utilities"
Cohesion: 0.32
Nodes (7): django_utils_text, english_slug(), polish_to_ascii(), Slugi katalogu — angielskie, unikalne, niezmienne po opublikowaniu. Zasada jest…, Zamienia gotowy tekst na slug. Nie tłumaczy niczego., Slug z angielskiego brzmienia pola `field`. Kolejność jest celowa: najpierw…, slugify_name()

### Community 88 - "Product Filter Tests E"
Cohesion: 0.25
Nodes (6): integration, django_db, Wybór realizacji zależy od silnika połączenia, nie od ustawień testów., Gałąź produkcyjna: pełnotekstowe wyszukiwanie PostgreSQL., TestSearchEngineSeam, TestSearchOnPostgres

### Community 89 - "Gemstone Model"
Cohesion: 0.25
Nodes (4): Gemstone, Meta, Klucz dokumentu w buckecie — bez hosta i bez nazwy bucketa., Kamień osadzony w wariancie (`CONTEXT.md`, Gemstone). Wariant może mieć wiele…

### Community 90 - "Image Model Tests"
Cohesion: 0.29
Nodes (5): Any, validate_original_size(), django_db, Oryginał ma limit dziesięciu megabajtów., TestOriginalLimit

### Community 91 - "Product Celery Tasks"
Cohesion: 0.32
Nodes (7): notify_owner_about_rate_activation(), shared_task, Przelicza ceny wariantów po zatwierdzeniu kursu (ADR 0022)., Wiadomość do właściciela po każdej aktywacji kursu. Aktywacja przecenia cały…, Tnie oryginał do kadru i zapisuje trzy rozmiary WebP (ADR 0025). Oryginał…, recalculate_variant_prices(), render_product_image()

### Community 92 - "Category Model Tests B"
Cohesion: 0.25
Nodes (3): django_db, Narzut domyślny kategorii: procent albo kwota, nigdy oba (ADR 0022)., TestMargin

### Community 94 - "Translation Test Helpers"
Cohesion: 0.25
Nodes (5): BrokenProvider, Silnik tłumaczeń na potrzeby testów. Produkcja ma DeepL albo LibreTranslate;…, Doklejka do tekstu, żeby po wyniku było widać, że przeszedł silnik. Prefiks…, Silnik, który nie odpowiada — do testów odmowy zapisu., StubProvider

### Community 95 - "Consent Model Core"
Cohesion: 0.38
Nodes (4): ConsentDocumentQuerySet, Wersje, które już obowiązują — przyszła wersja jeszcze nie jest bieżąca., Bieżąca wersja dokumentu danego rodzaju; `None`, gdy żadnej nie ma., Po jednej bieżącej wersji na rodzaj, w kolejności rodzajów.

### Community 96 - "Consent Model Tests C"
Cohesion: 0.29
Nodes (3): django_db, Bieżąca wersja to najnowsza, która już obowiązuje — nie najnowsza w ogóle., TestCurrentDocument

### Community 97 - "API Conventions Tests B"
Cohesion: 0.29
Nodes (3): Limity żądań: anonim 60/min, zalogowany 300/min, zakres `auth` 10/min., Zakres `auth` czeka gotowy — sam z siebie nie ogranicza niczego., TestThrottling

### Community 98 - "Celery Bootstrap"
Cohesion: 0.33
Nodes (4): celery, debug_task(), Wczytanie aplikacji Celery razem z Django. Bez tego `shared_task(...).delay()`…, task

### Community 100 - "Integration Fixtures"
Cohesion: 0.40
Nodes (5): mock_redis_connection(), mock_s3_storage(), fixture, Wyłącza globalny mock Redis — testy integracyjne mają używać prawdziwego Redis., Wyłącza globalny mock S3 — testy integracyjne mają używać prawdziwego MinIO/S3.

### Community 102 - "Catalog Factories"
Cohesion: 0.50
Nodes (3): factory_declarations, factory_django, factory_helpers

### Community 103 - "Product View Helpers"
Cohesion: 0.40
Nodes (3): OrderingFilter, ProductOrderingFilter, Sortowanie po nazwach z listy, nie po nazwach kolumn. `?ordering=price` musi…

### Community 104 - "Consent Model Helpers"
Cohesion: 0.50
Nodes (3): ConsentQuerySet, Zgody użytkownika albo gościa po e-mailu — nigdy obu naraz. Zgoda gościa nie…, Czy podmiot zaakceptował bieżącą wersję dokumentu danego rodzaju.

### Community 105 - "Cost Component Model"
Cohesion: 0.40
Nodes (3): CostComponent, Meta, Nazwana pozycja kosztu wykonania wariantu (`CONTEXT.md`, CostComponent).…

### Community 106 - "Pricing Rounding Tests"
Cohesion: 0.40
Nodes (4): round_up_to_zloty(), parametrize, Cena kończy się na pełnych złotówkach, zawsze w górę., TestRounding

### Community 108 - "API Conventions Tests D"
Cohesion: 0.40
Nodes (3): parametrize, Porządek modeli ma rozstrzygnięcie remisu — inaczej paginacja kłamie.…, TestOrdering

### Community 116 - "Filter Test Catalog"
Cohesion: 0.67
Nodes (3): catalog(), fixture, Mały katalog, w którym każda cecha różni dokładnie jedną parę.

## Knowledge Gaps
- **42 isolated node(s):** `backend`, `Migration`, `Migration`, `Meta`, `Meta` (+37 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 834 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **88 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `TimestampedModel` connect `Money Fields & Slugs` to `Product Model & Admin`, `Product Choices & Gemstone`, `Address & Profile Views`, `Accounts Migrations`, `API Conventions Tests A`, `Profile Model & Service`, `Translation Service & Models`, `Metal Rate Admin`, `Category Model & Admin`, `Consent Serializers & Views`, `Translation Admin`, `Collection Model & Admin`, `Product Variant Model`, `Consent Model Tests A`, `Inventory Model & Admin`, `Stock in Product View`, `Consent Models`, `Product Image Model`, `Gemstone Model`, `Cost Component Model`?**
  _High betweenness centrality (0.098) - this node is a cross-community bridge._
- **Why does `ProfileFactory` connect `Account Service Tests` to `Account Test Fixtures`, `Account Model Tests`, `API Conventions Tests A`, `Profile Serializers`, `Account View Tests`?**
  _High betweenness centrality (0.081) - this node is a cross-community bridge._
- **Why does `PublishedProductFactory` connect `Product Views Tests` to `Collections Tests`, `Gemstone Tests`, `Product Choices & Gemstone`, `Product Model Tests A`, `Translation Service & Models`, `Translation Warnings Tests`, `Metal Rate Pricing Tests`, `Pricing Engine Tests`, `Product Model Tests B`, `Product Image Tests A`, `Inventory Model Tests`, `Translation Tasks`, `Image Processing`, `Translation Service Tests`, `Inventory Tests C`, `Translation Fallback Tests`, `Product Filter Tests B`, `Product Filter Tests C`, `Product Filter Tests D`, `Image Tests B`, `Translation Admin Tests`, `Image Tests C`, `Inventory Tests D`, `Image Tests D`, `Filter Test Catalog`?**
  _High betweenness centrality (0.079) - this node is a cross-community bridge._
- **Are the 30 inferred relationships involving `PublishedProductFactory` (e.g. with `TestMembership` and `TestCollectionListAccess`) actually correct?**
  _`PublishedProductFactory` has 30 INFERRED edges - model-reasoned connections that need verification._
- **Are the 25 inferred relationships involving `Money` (e.g. with `Category` and `CostComponent`) actually correct?**
  _`Money` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 24 inferred relationships involving `CategoryFactory` (e.g. with `TestMargin` and `TestSlug`) actually correct?**
  _`CategoryFactory` has 24 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `ProductVariantFactory` (e.g. with `catalog()` and `TestFeatureFilters`) actually correct?**
  _`ProductVariantFactory` has 18 INFERRED edges - model-reasoned connections that need verification._