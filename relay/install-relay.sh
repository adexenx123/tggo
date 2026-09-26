#!/bin/sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
target=${TGGO_RELAY_DIR:-"$HOME/.local/lib/tggo-relay"}
mkdir -p "$target/src"
chmod 700 "$target"
cp "$root/relay/tggo-relay.py" "$target/tggo-relay.py"
rm -rf "$target/src/tggo"
cp -R "$root/src/tggo" "$target/src/tggo"
chmod 700 "$target/tggo-relay.py"
echo "Relay installed at $target"
