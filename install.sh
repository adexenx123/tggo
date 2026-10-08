#!/bin/sh
set -eu

root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
codex_root=${CODEX_HOME:-"$HOME/.codex"}
lib_root="$HOME/.local/lib/tggo"
bin_root="$HOME/.local/bin"
config_root="$HOME/.config/tggo"
skill_root="$codex_root/skills/tggo"
stage=$(mktemp -d "${TMPDIR:-/tmp}/tggo-install.XXXXXXXX")
trap 'rm -rf "$stage"' EXIT HUP INT TERM

mkdir -p "$stage/app/src" "$stage/app/relay" "$stage/app/service"
cp -R "$root/src/tggo" "$stage/app/src/tggo"
cp "$root/relay/tggo-relay.py" "$stage/app/relay/tggo-relay.py"
cp "$root/relay/install-relay.sh" "$stage/app/relay/install-relay.sh"
cp "$root/.env.example" "$stage/app/.env.example"
cp "$root/service/com.tggo.inbox.plist" "$stage/app/service/com.tggo.inbox.plist"
cp "$root/service/tggo-inbox.service" "$stage/app/service/tggo-inbox.service"

mkdir -p "$(dirname "$lib_root")" "$bin_root" "$config_root" "$(dirname "$skill_root")"
chmod 700 "$config_root"
rm -rf "$lib_root.new"
mv "$stage/app" "$lib_root.new"
rm -rf "$lib_root"
mv "$lib_root.new" "$lib_root"

wrapper="$bin_root/tggo"
printf '%s\n' '#!/bin/sh' 'set -eu' 'PYTHONPATH="$HOME/.local/lib/tggo/src${PYTHONPATH:+:$PYTHONPATH}" exec python3 -m tggo.cli "$@"' > "$wrapper"
chmod 700 "$wrapper"

rm -rf "$skill_root.new"
mkdir -p "$skill_root.new"
cp -R "$root/tggo/." "$skill_root.new/"
rm -rf "$skill_root"
mv "$skill_root.new" "$skill_root"

if [ ! -f "$config_root/config.env" ]; then
  cp "$root/.env.example" "$config_root/config.env"
fi
chmod 600 "$config_root/config.env"

case "$(uname -s)" in
  Darwin)
    service_root="$HOME/Library/LaunchAgents"
    mkdir -p "$service_root" "$HOME/Library/Logs"
    sed -e "s|__TGGO_BIN__|$wrapper|g" -e "s|__TGGO_LOG__|$HOME/Library/Logs/tggo-inbox.log|g" "$root/service/com.tggo.inbox.plist" > "$service_root/com.tggo.inbox.plist"
    printf '%s\n' "To enable: launchctl bootstrap gui/$(id -u) $service_root/com.tggo.inbox.plist"
    ;;
  Linux)
    service_root="$HOME/.config/systemd/user"
    mkdir -p "$service_root"
    cp "$root/service/tggo-inbox.service" "$service_root/tggo-inbox.service"
    printf '%s\n' "To enable: systemctl --user daemon-reload && systemctl --user enable --now tggo-inbox.service"
    ;;
esac

printf '%s\n' "TGGO installed. Inbox service was installed but not started." "1. Edit $config_root/config.env" "2. Run $wrapper doctor" "3. Invoke \$tggo in Codex"
