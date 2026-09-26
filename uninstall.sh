#!/bin/sh
set -eu

codex_root=${CODEX_HOME:-"$HOME/.codex"}
rm -f "$HOME/.local/bin/tggo"
rm -rf "$HOME/.local/lib/tggo"
rm -rf "$codex_root/skills/tggo"

if [ "${1:-}" = "--purge" ]; then
  rm -rf "$HOME/.config/tggo"
  rm -rf "$HOME/.local/state/tggo"
  echo "TGGO removed, including configuration and state."
else
  echo "TGGO removed. Configuration and state were preserved."
fi
