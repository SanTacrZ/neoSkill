#!/usr/bin/env bash
# Publica docs/wiki/ en la wiki de GitHub del repositorio.
# Requisito: la wiki habilitada en Settings → Features → Wikis.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "→ Clonando la wiki..."
git clone --depth 1 git@github.com:SanTacrZ/neoSkill.wiki.git "$TMP/wiki"

echo "→ Copiando páginas desde docs/wiki/..."
cp "$ROOT"/docs/wiki/*.md "$TMP/wiki/"

cd "$TMP/wiki"
git add -A
if git diff --cached --quiet; then
  echo "✓ La wiki ya está actualizada."
  exit 0
fi

git -c user.name="$(git -C "$ROOT" config user.name)" \
    -c user.email="$(git -C "$ROOT" config user.email)" \
    commit -m "Actualiza wiki desde docs/wiki/"
git push origin master
echo "✓ Wiki publicada: https://github.com/SanTacrZ/neoSkill/wiki"
