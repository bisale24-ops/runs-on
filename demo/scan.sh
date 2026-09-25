#!/usr/bin/env bash
# Reproduce the table in README.md: clone each project and check its promise.
#   ./demo/scan.sh [directory-to-clone-into]
set -uo pipefail
cd "$(dirname "$0")/.."
WORK="${1:-/tmp/runs-on-scan}"
mkdir -p "$WORK"

REPOS="Textualize/rich pallets/click encode/httpx fastapi/typer psf/black python-poetry/poetry
mkdocs/mkdocs theskumar/python-dotenv Delgan/loguru tiangolo/sqlmodel pallets/itsdangerous
msiemens/tinydb sdispater/pendulum agronholm/apscheduler jd/tenacity astanin/python-tabulate
psf/requests urllib3/urllib3 pallets/jinja pallets/werkzeug pallets/markupsafe pypa/packaging
tqdm/tqdm arrow-py/arrow python-humanize/humanize tkem/cachetools GrahamDumpleton/wrapt
more-itertools/more-itertools kennethreitz/records psf/requests-html"

for repo in $REPOS; do
  name="${repo##*/}"
  [ -d "$WORK/$name" ] || git clone -q --depth 1 "https://github.com/$repo.git" "$WORK/$name"
  printf '%-16s ' "$name"
  PYTHONPATH=src python3 -m runson.cli --repo "$WORK/$name" --quiet 2>/dev/null | tail -1
done
