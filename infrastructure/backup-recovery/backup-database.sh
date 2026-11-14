#!/usr/bin/env bash
set -euo pipefail
umask 077
out=${1:?Usage: backup-database.sh OUTPUT.dump}
tmp=$(mktemp -- "${out}.part.XXXXXX")
trap 'rm -f -- "$tmp"' EXIT
docker compose exec -T db pg_dump -U postgres -Fc yukti > "$tmp"
test -s "$tmp"
mv -n -- "$tmp" "$out"
if [ -e "$tmp" ]; then
  printf 'Output already exists: %s\n' "$out" >&2
  exit 1
fi
