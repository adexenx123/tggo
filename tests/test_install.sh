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
test -f "$HOME/.local/lib/tggo/service/com.tggo.inbox.plist"
test -f "$HOME/.local/lib/tggo/service/tggo-inbox.service"
permission=$(python3 -c 'import os,sys; print(oct(os.stat(sys.argv[1]).st_mode & 0o777)[2:])' "$HOME/.config/tggo/config.env")
test "$permission" = 600
printf '\nCUSTOM_MARKER=keep\n' >> "$HOME/.config/tggo/config.env"

"$repo/install.sh"
grep -q CUSTOM_MARKER "$HOME/.config/tggo/config.env"

"$repo/uninstall.sh"
test ! -e "$HOME/.local/bin/tggo"
test -f "$HOME/.config/tggo/config.env"

"$repo/install.sh"
mkdir -p "$HOME/.local/state/tggo"
: > "$HOME/.local/state/tggo/ledger.json"
mkdir -p "$HOME/.local/share/tggo/inbox"
: > "$HOME/.local/share/tggo/inbox/index.json"
"$repo/uninstall.sh"
test -f "$HOME/.local/share/tggo/inbox/index.json"
"$repo/install.sh"
"$repo/uninstall.sh" --purge
test ! -e "$HOME/.config/tggo"
test ! -e "$HOME/.local/state/tggo"
test ! -e "$HOME/.local/share/tggo"

echo "install tests passed"
