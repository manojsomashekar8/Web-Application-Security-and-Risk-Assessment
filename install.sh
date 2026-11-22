#!/usr/bin/env bash
# Set up WASRA on a fresh Ubuntu host. Idempotent: safe to run twice.
#   ./install.sh            install what is missing, create .env if absent, build and start the stack
#   ./install.sh --check    report what is missing and the resource check; change nothing
#   ./install.sh --no-start install and build, but do not start the stack
set -euo pipefail

CHECK_ONLY=0; NO_START=0
for arg in "$@"; do
  case "$arg" in
    --check) CHECK_ONLY=1 ;;
    --no-start) NO_START=1 ;;
    -h|--help) sed -n '2,5p' "$0"; exit 0 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

# Minimum host needs. Measured values are in docs/REPRODUCIBILITY.md; these are the warning thresholds.
MIN_RAM_GB=16
MIN_FREE_GB=25

say() { printf '%s\n' "$*"; }
die() { printf 'error: %s\n' "$*" >&2; exit 1; }

# 1. OS: only Ubuntu 22.04 and 24.04 are tested.
[ -r /etc/os-release ] || die "cannot read /etc/os-release; unsupported system"
. /etc/os-release
if [ "${ID:-}" != "ubuntu" ] || { [ "${VERSION_ID:-}" != "22.04" ] && [ "${VERSION_ID:-}" != "24.04" ]; }; then
  die "unsupported system: ${PRETTY_NAME:-unknown}. This script supports Ubuntu 22.04 and 24.04."
fi
say "OS: ${PRETTY_NAME}"

# 2. Resources
ram_gb=$(awk '/MemTotal/ {printf "%d", $2/1024/1024}' /proc/meminfo)
free_gb=$(df -BG --output=avail "$(pwd)" | tail -1 | tr -dc '0-9')
say "RAM: ${ram_gb} GB (recommended ${MIN_RAM_GB} GB); free disk here: ${free_gb} GB (recommended ${MIN_FREE_GB} GB)"
[ "$ram_gb" -lt "$MIN_RAM_GB" ] && say "warning: less RAM than recommended; scans may be slow or fail"
[ "$free_gb" -lt "$MIN_FREE_GB" ] && say "warning: less free disk than recommended"

need=()
command -v git >/dev/null || need+=(git)
command -v make >/dev/null || need+=(make)
command -v python3.12 >/dev/null || python3 -c 'import sys; sys.exit(0 if sys.version_info[:2]==(3,12) else 1)' 2>/dev/null || need+=(python3.12)
command -v curl >/dev/null || need+=(curl)
command -v docker >/dev/null || need+=(docker)
docker compose version >/dev/null 2>&1 || need+=(compose)

if [ "$CHECK_ONLY" -eq 1 ]; then
  if [ ${#need[@]} -eq 0 ]; then say "all prerequisites present"; else say "missing: ${need[*]}"; fi
  exit 0
fi

# 3. Install what is missing, from Ubuntu's archive or Docker's official repository.
if [ ${#need[@]} -gt 0 ]; then
  say "installing: ${need[*]}"
  sudo apt-get update
  for item in "${need[@]}"; do
    case "$item" in
      git|make|curl) sudo apt-get install -y "$item" ;;
      python3.12) sudo apt-get install -y python3.12 python3.12-venv ;;
      docker|compose)
        # Docker's documented repository: add its signing key from download.docker.com, then the package list.
        sudo apt-get install -y ca-certificates curl
        sudo install -m 0755 -d /etc/apt/keyrings
        sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
        sudo chmod a+r /etc/apt/keyrings/docker.asc
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" \
          | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
        sudo apt-get update
        sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
        sudo usermod -aG docker "$USER" || true
        ;;
    esac
  done
else
  say "prerequisites already installed"
fi

# 4. Settings file: created once, never overwritten.
if [ -f .env ]; then
  say ".env exists; keeping it"
else
  make env
  say "created .env with random passwords"
fi

# 5. Virtualenv for tests and host tools (idempotent).
[ -x .venv/bin/python ] || make venv

# 6. Build and start, then wait for the health endpoints.
if [ "$NO_START" -eq 1 ]; then
  say "built nothing: --no-start given. Run 'make up' to start."
  exit 0
fi
make up

auth_mode=$(grep -E '^AUTH_MODE=' .env | cut -d= -f2 || true)
say ""
say "WASRA is running."
say "  Web app (React):   http://127.0.0.1"
say "  Original pages:    http://127.0.0.1:8080"
say "  Dashboards:        http://127.0.0.1:3001"
say "  Login mode:        ${auth_mode:-none} (set AUTH_MODE in .env; see docs/HOW_TO_START.md)"
