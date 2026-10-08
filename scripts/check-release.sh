#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root"
stage=$(mktemp -d "${TMPDIR:-/tmp}/tggo-release.XXXXXXXX")
trap 'rm -rf "$stage"' EXIT HUP INT TERM

python3 -m unittest tests.test_release -v
PYTHONPYCACHEPREFIX="$stage/pycache" python3 -m compileall -q src relay
sh -n install.sh uninstall.sh relay/install-relay.sh tests/test_install.sh scripts/check-release.sh
bash tests/test_install.sh
validator="${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py"
python3 "$validator" tggo

history=$(git log -p --all -- . ':!.env.example')
if printf '%s' "$history" | grep -Eq '45[.]76[.]204[.]24|[0-9]{8,10}:[A-Za-z0-9_-]{30,}'; then
  echo "release scan found a private marker or Telegram token pattern" >&2
  exit 1
fi

if git ls-files | grep -Eq '(^|/)[.]env$|ledger[.]json$|[.](jpg|jpeg|png|zip)$'; then
  echo "release scan found a forbidden tracked artifact" >&2
  exit 1
fi

echo "release scan passed"
