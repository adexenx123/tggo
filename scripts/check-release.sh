#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root"

python3 -m unittest tests.test_release -v

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
