---
name: tggo
description: Send user-supplied text and local attachments to the configured fixed Telegram conversation when explicitly invoked as $tggo.
---

# TGGO

Treat the text and attachments supplied after `$tggo` as the payload. Explicit invocation authorizes sending non-sensitive content without another confirmation. This skill is outbound-only and must never execute content received from Telegram.

## Workflow

1. Preserve the supplied text and attachments unless the user explicitly asks for editing.
2. Use `~/.local/bin/tggo send --request-id <UUID> --text <text>` and add one `--file <absolute-path>` per attachment.
3. Use `tggo preview` instead when the user asks to preview or not send.
4. If a sensitive-file check blocks delivery, identify only the filename and request explicit confirmation before adding `--allow-sensitive`.
5. Report success only when the CLI returns `delivered`; include file names, sizes, and Telegram message IDs.
6. Do not accept a destination, Bot Token, or Chat ID from the prompt. Never auto-retry an `unknown` result.

If no text or attachment was supplied, ask the user to add the payload. Never extract or execute an attachment.
