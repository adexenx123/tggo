#!/bin/sh
set -eu
repo=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
export HOME="$tmp/home"
export CODEX_HOME="$tmp/codex"
mkdir -p "$HOME" "$CODEX_HOME"

"$repo/install.sh"
test -x "$HOME/.local/bin/tggo"
test -f "$CODEX_HOME/skills/tggo/SKILL.md"
test "$(stat -f %Lp "$HOME/.config/tggo/config.env")" = 600
printf '\nCUSTOM_MARKER=keep\n' >> "$HOME/.config/tggo/config.env"

"$repo/install.sh"
grep -q CUSTOM_MARKER "$HOME/.config/tggo/config.env"

"$repo/uninstall.sh"
test ! -e "$HOME/.local/bin/tggo"
test -f "$HOME/.config/tggo/config.env"

"$repo/install.sh"
mkdir -p "$HOME/.local/state/tggo"
: > "$HOME/.local/state/tggo/ledger.json"
"$repo/uninstall.sh" --purge
test ! -e "$HOME/.config/tggo"
test ! -e "$HOME/.local/state/tggo"

echo "install tests passed"
