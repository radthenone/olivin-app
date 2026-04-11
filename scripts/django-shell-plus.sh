#!/usr/bin/env bash
set -o errexit
set -o pipefail
set -o nounset

CONTAINER_NAME="${1:-olivin-django}"
APP_DIR="${2:-/app/src}"
VENV_PYTHON="${3:-/app/.venv/bin/python}"

docker exec -it "$CONTAINER_NAME" bash -lc '
  set -o errexit
  set -o pipefail
  set -o nounset

  APP_DIR="'"$APP_DIR"'"
  VENV_PYTHON="'"$VENV_PYTHON"'"

  cd "$APP_DIR"

  IPYTHONDIR="$(mktemp -d)"
  cleanup() {
    rm -rf "$IPYTHONDIR"
  }
  trap cleanup EXIT INT TERM

  STARTUP_DIR="$IPYTHONDIR/profile_default/startup"
  mkdir -p "$STARTUP_DIR"

  cat > "$STARTUP_DIR/00-autoreload.py" <<'"'"'PY'"'"'
from IPython import get_ipython

ip = get_ipython()
if ip is not None:
    ip.run_line_magic("load_ext", "autoreload")
    ip.run_line_magic("autoreload", "2")
PY

  export IPYTHONDIR

  "$VENV_PYTHON" manage.py shell_plus --ipython
'
