# Projekt

## Konfiguracja

### backend

```bash
cd backend
uv sync --all-extras
uv pip install "pack-logger[django] @ git+https://github.com/radthenone/pack-logger.git@v0.1.0#subdirectory=backend"
docker-compose --profile backend up --build -d
```

### frontend

```bash
cd frontend
bun add "git+https://github.com/radthenone/pack-logger.git#v0.1.0"
bun install
```

## Uruchomienie

### backend

```bash
make backend
```

### android

```bash
przed uruchomieniem uruchom emulator android
avdmanager list avd # lista emulatorów
emulator -avd <nazwa_emulatora_z_listy> # najczesciej S23 S23-Ultra
#wtedy
make android
```

### frontend

```bash
make web
```
