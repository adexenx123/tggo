#!/bin/sh
set -eu

codex_root=${CODEX_HOME:-"$HOME/.codex"}
rm -f "$HOME/.local/bin/tggo"
rm -rf "$HOME/.local/lib/tggo"
rm -rf "$codex_root/skills/tggo"
rm -f "$HOME/Library/LaunchAgents/com.tggo.inbox.plist"
rm -f "$HOME/.config/systemd/user/tggo-inbox.service"

if [ "${1:-}" = "--purge" ]; then
  rm -rf "$HOME/.config/tggo"
  rm -rf "$HOME/.local/state/tggo"
  rm -rf "$HOME/.local/share/tggo"
  echo "TGGO removed, including configuration, state, and inbox data."
else
  echo "TGGO removed. Configuration, state, and inbox data were preserved."
fi
