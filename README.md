# TGGO

[繁體中文](#繁體中文) · [English](#english)

## 繁體中文

TGGO 是一個功能刻意限縮的 Codex Skill，用來將使用者明確指定的文字與本機附件傳送到固定的 Telegram 對話。它不允許 Telegram 執行 Codex、Shell 指令或伺服器操作。

### 功能

- 只有明確呼叫 `$tggo` 才會執行
- 支援文字、圖片、影片、GIF、音訊、語音及一般文件
- 長文自動分段，多張圖片／影片自動組成相簿
- 檢查敏感檔案、符號連結、單檔大小與單次總容量
- 提供 SHA-256、Telegram Message ID 與防重複傳送機制
- 支援 `direct` 與選用的 `ssh-relay` 傳送模式
- 支援不產生網路副作用的傳送前預覽

### 系統需求

- macOS 或 Linux
- Python 3.9 以上
- `curl`
- 使用 `ssh-relay` 模式時需要 OpenSSH
- 透過 BotFather 建立的 Telegram Bot

Telegram 設定會使用兩個不同的值：

- `TGGO_BOT_TOKEN`：BotFather 發給你的機密 Token，請勿公開或提交到 Git。
- `TGGO_CHAT_ID`：Bot 要傳送訊息的數字對話 ID；它不是 Bot 使用者名稱，也不是 Bot ID。

### 安裝

```bash
git clone https://github.com/adexenx123/tggo.git
cd tggo
./install.sh
```

安裝程式會把執行程式複製到 `~/.local/lib/tggo`，將 Skill 安裝到 `${CODEX_HOME:-~/.codex}/skills/tggo`，並建立權限為 `0600` 的 `~/.config/tggo/config.env`。安裝過程不會自動傳送測試訊息。

確認 `~/.local/bin` 已加入 `PATH`，然後編輯設定：

```bash
chmod 600 ~/.config/tggo/config.env
${EDITOR:-vi} ~/.config/tggo/config.env
tggo doctor
tggo test
```

`tggo test` 會刻意傳送一則標示清楚的測試訊息。

### Direct 模式

如果執行 Codex 的電腦可以直接連線至 Telegram，請使用此模式：

```env
TGGO_MODE=direct
TGGO_BOT_TOKEN=填入你的-bot-token
TGGO_CHAT_ID=填入你的-chat-id
TGGO_MAX_FILE_MB=50
TGGO_MAX_TOTAL_MB=200
TGGO_TELEGRAM_API_BASE=https://api.telegram.org
```

### SSH Relay 模式

如果希望改由另一台主機連線 Telegram，可使用 SSH Relay。先在 Relay 主機的專案副本中安裝：

```bash
./relay/install-relay.sh
mkdir -p ~/.config/tggo
chmod 700 ~/.config/tggo
cp .env.example ~/.config/tggo/relay.env
chmod 600 ~/.config/tggo/relay.env
```

將 Relay 主機的 `relay.env` 設為 `TGGO_MODE=direct`，並填入該主機使用的 `TGGO_BOT_TOKEN` 與 `TGGO_CHAT_ID`。接著在 Codex 電腦設定：

```env
TGGO_MODE=ssh-relay
TGGO_BOT_TOKEN=
TGGO_CHAT_ID=
TGGO_SSH_HOST=relay.example.com
TGGO_SSH_USER=你的使用者名稱
TGGO_SSH_PORT=22
TGGO_SSH_IDENTITY_FILE=~/.ssh/id_ed25519
TGGO_REMOTE_ENV_FILE=~/.config/tggo/relay.env
```

本機傳送清單不會包含 Relay 的 Bot Token 或 Chat ID，Relay 也不會開放公網 HTTP API。

### 在 Codex 中使用

```text
$tggo 把這段文字傳到 Telegram。
```

要傳送附件時，將檔案附在同一個 Codex 請求即可。TGGO 會保留使用者提供的內容，且只會傳送到設定檔指定的對話。

CLI 範例：

```bash
tggo preview --text '本週報告' --file /absolute/report.pdf
tggo send --request-id "$(uuidgen)" --text '本週報告' --file /absolute/report.pdf
tggo doctor
```

`.env`、私鑰、憑證及 credential store 等敏感檔案名稱預設會被阻擋。確認實際檔案與目的地後，可使用 `--allow-sensitive` 明確授權單次傳送。

### 解除安裝

移除程式與 Skill，但保留設定和傳送狀態：

```bash
./uninstall.sh
```

連設定與狀態一起移除：

```bash
./uninstall.sh --purge
```

### 限制

預設容量限制依照本套件使用的 Telegram Cloud Bot API 設定。TGGO 不會壓縮、拆分、解壓或執行檔案。當網路結果無法確認時，會記錄為 `unknown`，而且不會自動重送。

部署 SSH Relay 前，請先閱讀 [SECURITY.md](SECURITY.md)。

---

## English

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
git clone https://github.com/adexenx123/tggo.git
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
