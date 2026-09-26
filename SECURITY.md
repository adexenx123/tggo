# Security Policy

## Scope and threat model

TGGO is an outbound-only delivery tool. Its security boundary is one locally configured Telegram chat. Prompt text cannot override the Bot Token, Chat ID, SSH destination, or relay environment file.

TGGO assumes the local Codex user and the configured SSH account are trusted. It does not make an untrusted multi-user workstation safe and must not be installed setuid or run as root.

## Secrets

- Store configuration at `~/.config/tggo/config.env` with mode `0600`.
- Never commit a real `.env`, Bot Token, Chat ID, SSH private key, or delivery ledger.
- In `ssh-relay` mode, keep Telegram credentials only in the relay environment file. The transfer manifest contains no destination credentials.
- Telegram URLs containing the Bot Token are passed to curl over stdin rather than process arguments.

## Attachments

TGGO rejects symbolic links, directories, device files, oversized files, and common secret or credential filenames. It never extracts or executes attachments. File type detection controls Telegram presentation only; it is not malware detection.

Before using `--allow-sensitive`, independently inspect the exact file and confirm that Telegram is an acceptable destination. Full payment-card data, passwords, private keys, authentication cookies, and recovery codes should not be transmitted.

## Delivery uncertainty

Request IDs are recorded before transmission. When the sender cannot determine whether Telegram accepted a request, the ledger records `unknown`; TGGO does not retry automatically. This prevents silent duplicate delivery but requires human review.

## SSH Relay

- Use key authentication and a dedicated non-root account.
- Restrict the SSH key in `authorized_keys` when practical.
- Keep the relay environment file at mode `0600`.
- Do not expose the relay through a public HTTP endpoint.
- Review and patch the relay host like any system that stores a Telegram Bot Token.

## Reporting a vulnerability

Do not include real tokens, private files, or exploitable production details in a public issue. Contact the repository maintainer privately and provide a minimal reproduction using fake credentials.
