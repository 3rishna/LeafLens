#!/usr/bin/env bash
# Rebuild the Overleaf upload package after editing paper/main.tex or the figures.
#
# sn-jnl.cls is Springer's class; it is not on CTAN, is not committed to this repo,
# and Overleaf will not supply it automatically, so it must be bundled. Pass the path
# to your copy (from the Springer Nature Overleaf template or Springer's author-support
# download) as the first argument, or place it at paper/sn-jnl.cls.
set -euo pipefail
cd "$(dirname "$0")/.."

CLS="${1:-paper/sn-jnl.cls}"
if [[ ! -f "$CLS" ]]; then
  echo "error: sn-jnl.cls not found at '$CLS'"
  echo "       pass its path:  scripts/make_overleaf_package.sh /path/to/sn-jnl.cls"
  exit 1
fi

OUT="LeafLens_overleaf.zip"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

cp paper/main.tex "$STAGE/"
cp "$CLS" "$STAGE/sn-jnl.cls"
mkdir -p "$STAGE/figures"
# copy only the figures main.tex actually references
grep -o 'figures/[A-Za-z0-9_]*\.\(png\|jpg\)' paper/main.tex | sort -u | while read -r f; do
  cp "paper/$f" "$STAGE/$f"
done
[[ -f paper/OVERLEAF_README.txt ]] && cp paper/OVERLEAF_README.txt "$STAGE/README.txt"

rm -f "$OUT"
( cd "$STAGE" && zip -qr9 "$OLDPWD/$OUT" . )
echo "wrote $OUT"
unzip -l "$OUT" | tail -n +2
