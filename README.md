# TGGO

TGGO is a deliberately narrow Codex Skill that sends user-approved text and local attachments to one configured Telegram conversation. It does not let Telegram execute Codex, shell commands, or server operations.

## Features

- Explicit `$tggo` invocation only
- Text, photos, video, GIF, audio, voice, and general documents
- Automatic long-text splitting and photo/video albums
- Sensitive-file, symlink, per-file, and total-size checks
- SHA-256 receipts, Telegram message IDs, and duplicate request protection
- `direct` and optional `ssh-relay` delivery modes
- Preview without network side effects

## Requirements

- macOS or Linux
- Python 3.9 or newer
- `curl`
- OpenSSH for `ssh-relay` mode
- A Telegram bot created with BotFather

Telegram uses two different values:

- `TGGO_BOT_TOKEN`: the secret token issued by BotFather. Keep it private.
- `TGGO_CHAT_ID`: the numeric conversation ID that the bot may send to. This is not the bot's username or numeric bot ID.

## Install

```bash
git clone <repository-url> tggo
cd tggo
./install.sh
```

The installer copies the runtime to `~/.local/lib/tggo`, installs the Skill under `${CODEX_HOME:-~/.codex}/skills/tggo`, and creates `~/.config/tggo/config.env` with permission `0600`. It never sends a test message automatically.

Ensure `~/.local/bin` is in `PATH`, then edit the configuration:

```bash
chmod 600 ~/.config/tggo/config.env
${EDITOR:-vi} ~/.config/tggo/config.env
tggo doctor
tggo test
```

`tggo test` intentionally sends one clearly labelled test message.

## Direct mode

Use this when the Codex machine can reach Telegram directly:

```env
TGGO_MODE=direct
TGGO_BOT_TOKEN=replace-with-your-token
TGGO_CHAT_ID=replace-with-your-chat-id
TGGO_MAX_FILE_MB=50
TGGO_MAX_TOTAL_MB=200
TGGO_TELEGRAM_API_BASE=https://api.telegram.org
```

## SSH Relay mode

Use this when Telegram should be contacted by another machine. Install the relay from a clone on that machine:

```bash
./relay/install-relay.sh
mkdir -p ~/.config/tggo
chmod 700 ~/.config/tggo
cp .env.example ~/.config/tggo/relay.env
chmod 600 ~/.config/tggo/relay.env
```

Set the relay's `relay.env` to `TGGO_MODE=direct` with its own `TGGO_BOT_TOKEN` and `TGGO_CHAT_ID`. On the Codex machine, configure:

```env
TGGO_MODE=ssh-relay
TGGO_BOT_TOKEN=
TGGO_CHAT_ID=
TGGO_SSH_HOST=relay.example.com
TGGO_SSH_USER=your-user
TGGO_SSH_PORT=22
TGGO_SSH_IDENTITY_FILE=~/.ssh/id_ed25519
TGGO_REMOTE_ENV_FILE=~/.config/tggo/relay.env
```

The local manifest never contains the relay Bot Token or Chat ID. The relay has no public HTTP endpoint.

## Use in Codex

```text
$tggo Send this text to Telegram.
```

Attach files to the same Codex request to send them with the text. TGGO preserves the supplied content and sends only to the configured chat.

CLI examples:

```bash
tggo preview --text 'Weekly report' --file /absolute/report.pdf
tggo send --request-id "$(uuidgen)" --text 'Weekly report' --file /absolute/report.pdf
tggo doctor
```

Sensitive filenames such as `.env`, private keys, certificates, and credential stores are blocked. After inspecting the exact filename and contents, a user may explicitly authorize one delivery with `--allow-sensitive`.

## Uninstall

Remove the runtime and Skill while preserving configuration and delivery state:

```bash
./uninstall.sh
```

Remove configuration and state as well:

```bash
./uninstall.sh --purge
```

## Limits

The defaults match Telegram's cloud Bot API file limits used by this package. TGGO does not compress, split, extract, or execute files. An uncertain network result is recorded as `unknown` and is never retried automatically.

See [SECURITY.md](SECURITY.md) before deploying the SSH Relay.
