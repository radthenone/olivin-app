# Pack Logger - Konfiguracja Docker

## ✅ Co zostało skonfigurowane:

### 1. Dockerfile (`docker/backend/Dockerfile`)

Dodano kopiowanie paczek lokalnych:

```dockerfile
# Kopiuj paczki lokalne PRZED pyproject.toml
COPY packages/ /app/packages/

COPY backend/pyproject.toml backend/uv.lock ./

# Aktualizuj ścieżkę do paczki w pyproject.toml dla Docker
# Lokalnie: ../packages/pack-logger/backend
# W Dockerze: packages/pack-logger/backend
RUN sed -i "s|path = \"../packages/pack-logger/backend\"|path = \"packages/pack-logger/backend\"|g" pyproject.toml || true
```

**Wyjaśnienie:**
- W lokalnym środowisku: `pyproject.toml` jest w `backend/`, więc ścieżka to `../packages/pack-logger/backend`
- W Dockerze: `pyproject.toml` jest w `/app/`, a `packages/` są w `/app/packages/`, więc ścieżka to `packages/pack-logger/backend`

### 2. docker-compose.yml

Dodano volume mount dla development:

```yaml
volumes:
    - ./backend/src:/app/src:z
    - ./packages:/app/packages:z  # ← Dodano
```

**Wyjaśnienie:**
- W development mode: zmiany w `packages/` są widoczne od razu (hot reload)
- W production build: paczki są kopiowane podczas budowania obrazu

## 🔍 Weryfikacja

### Sprawdź czy paczka jest zainstalowana w kontenerze:

```bash
docker-compose exec olivin-django python -c "import pack_logger; print(pack_logger.__version__)"
```

### Sprawdź ścieżkę w pyproject.toml w kontenerze:

```bash
docker-compose exec olivin-django cat /app/pyproject.toml | grep pack-logger
```

Powinno pokazać:
```toml
pack-logger = { path = "packages/pack-logger/backend", editable = true }
```

## 📝 Uwagi

1. **Development**: Volume mount zapewnia hot reload - zmiany w `packages/` są widoczne od razu
2. **Production**: Paczki są kopiowane podczas `docker build` - nie potrzebujesz volume mount
3. **Build cache**: Docker cache'uje warstwę z `packages/`, więc rebuild jest szybki jeśli paczki się nie zmieniły

## 🚀 Gotowe!

Paczka `pack-logger` będzie poprawnie instalowana i dostępna w kontenerze Docker! 🎉

