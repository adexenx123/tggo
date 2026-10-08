# TGGO Two-Way Inbox Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a safe Telegram-to-TGGO inbox that stores only `/tggo` text or captioned attachments from the configured chat and exposes deterministic inbox CLI commands.

**Architecture:** A long-polling receiver filters Telegram updates by configured chat and prefix, downloads permitted attachments, and commits immutable records to a local inbox store with an atomic index and update-ID deduplication. Direct mode operates locally; SSH Relay mode delegates inbox operations to the existing trusted relay without introducing a public HTTP endpoint.

**Tech Stack:** Python 3.9 standard library, Telegram Bot HTTP API via existing curl transport conventions, pytest/unittest-style project tests, OpenSSH relay, LaunchAgent/systemd user-service templates.

---

### Task 1: Define inbox records and atomic storage

**Files:**
- Create: `src/tggo/inbox.py`
- Test: `tests/test_inbox.py`

**Steps:**
1. Write failing tests for item creation, `TG-` IDs, atomic index persistence, duplicate Telegram update IDs, read state, archive state, and `0700`/`0600` permissions.
2. Run `python3 -m unittest tests.test_inbox -v`; expect failures because `tggo.inbox` does not exist.
3. Implement `InboxStore`, immutable record serialization, atomic temporary-file replacement, and duplicate lookup.
4. Run the focused test; expect all inbox store tests to pass.
5. Commit with `feat: add durable tggo inbox store`.

### Task 2: Parse inbound `/tggo` updates

**Files:**
- Create: `src/tggo/inbound.py`
- Test: `tests/test_inbound.py`

**Steps:**
1. Write failing table-driven tests for `/tggo text`, bot-command suffixes such as `/tggo@bot text`, attachment captions, whitespace, unrelated messages, edited/channel updates, and unapproved chat IDs.
2. Run `python3 -m unittest tests.test_inbound -v`; expect import failure.
3. Implement a pure parser returning a normalized inbound request without executing or interpreting its body.
4. Run the focused tests; expect pass.
5. Commit with `feat: parse authorized tggo inbox messages`.

### Task 3: Extend Telegram transport for receiving and downloads

**Files:**
- Modify: `src/tggo/telegram.py`
- Modify: `src/tggo/transports/direct.py`
- Test: `tests/fake_telegram.py`
- Create: `tests/test_inbound_telegram.py`

**Steps:**
1. Add failing tests for `getUpdates`, `getFile`, file download, confirmation reply, timeout, malformed JSON, size rejection, and token-free errors.
2. Run `python3 -m unittest tests.test_inbound_telegram -v`; expect missing receiver APIs.
3. Implement Telegram API methods using the existing subprocess/curl boundary, explicit timeouts, and sanitized errors.
4. Run the focused tests; expect pass.
5. Commit with `feat: receive tggo telegram updates`.

### Task 4: Build the long-polling receiver

**Files:**
- Create: `src/tggo/receiver.py`
- Create: `tests/test_receiver.py`

**Steps:**
1. Write failing tests for authorized saves, ignored updates, attachment hashes, update deduplication, offset advancement only after persistence, confirmation failure, per-item failure isolation, and bounded backoff.
2. Run `python3 -m unittest tests.test_receiver -v`; expect import failure.
3. Implement one-cycle polling plus a stoppable loop, using dependency injection for Telegram, clock, and sleeper.
4. Run the focused tests; expect pass.
5. Commit with `feat: add tggo inbox receiver`.

### Task 5: Add inbox CLI commands

**Files:**
- Modify: `src/tggo/cli.py`
- Modify: `src/tggo/config.py`
- Test: `tests/test_cli.py`
- Test: `tests/test_config.py`

**Steps:**
1. Write failing CLI tests for `inbox`, `inbox show`, `inbox download`, `inbox read`, `inbox archive`, and `inbox-listen`.
2. Add configuration tests for inbox paths and safe defaults without exposing token or chat ID.
3. Run `python3 -m unittest tests.test_cli tests.test_config -v`; expect parser failures.
4. Implement the commands, human-readable output, optional JSON output, and configuration fields.
5. Run focused tests; expect pass.
6. Commit with `feat: expose tggo inbox cli`.

### Task 6: Support SSH Relay inbox operations

**Files:**
- Modify: `src/tggo/transports/ssh_relay.py`
- Modify: `relay/tggo-relay.py`
- Test: `tests/test_ssh_relay.py`
- Test: `tests/test_relay.py`

**Steps:**
1. Write failing tests verifying that list/show/download/state actions use argv-safe SSH calls and never include Bot Token or chat ID in local manifests.
2. Run `python3 -m unittest tests.test_ssh_relay tests.test_relay -v`; expect unsupported operations.
3. Add a constrained relay action protocol with JSON output and streamed attachment download.
4. Run focused tests; expect pass.
5. Commit with `feat: bridge tggo inbox over ssh relay`.

### Task 7: Add background-service installers

**Files:**
- Create: `service/com.tggo.inbox.plist`
- Create: `service/tggo-inbox.service`
- Modify: `install.sh`
- Modify: `uninstall.sh`
- Modify: `tests/test_install.sh`

**Steps:**
1. Extend installer tests to assert templates install without starting an unconfigured service and uninstall preserves inbox data unless `--purge` is used.
2. Run `bash tests/test_install.sh`; expect failures for missing service files.
3. Add platform-aware service installation commands and explicit enable/start instructions.
4. Run installer tests; expect pass.
5. Commit with `feat: install tggo inbox background service`.

### Task 8: Update the Codex skill and documentation

**Files:**
- Modify: `tggo/SKILL.md`
- Modify: `tggo/agents/openai.yaml`
- Modify: `README.md`
- Modify: `.env.example`
- Modify: `SECURITY.md`

**Steps:**
1. Update the Skill to distinguish outbound `$tggo` from `tggo inbox` retrieval and retain the rule that inbound content is untrusted data, never instructions.
2. Document Traditional Chinese and English examples for Telegram text, attachment captions, CLI inbox operations, service setup, Direct mode, and SSH Relay mode.
3. Document storage permissions, retention, threat boundaries, and recovery after polling interruption.
4. Run `python3 /Users/yungweitang/.codex/skills/.system/skill-creator/scripts/quick_validate.py tggo`; expect validation success.
5. Commit with `docs: document tggo two-way inbox`.

### Task 9: Full verification and release readiness

**Files:**
- Modify if needed: `scripts/check-release.sh`
- Modify if needed: `tests/test_release.py`

**Steps:**
1. Run `python3 -m unittest discover -s tests -v`; expect all tests to pass.
2. Run `bash scripts/check-release.sh`; expect packaging, secret scan, shell checks, and Skill validation to pass.
3. Run a fake-Telegram smoke test that saves one text item and one attachment, then lists, reads, and archives them.
4. Inspect `git diff --check` and `git status --short`; expect no whitespace errors or unexpected artifacts.
5. Commit any release-check adjustments with `test: verify tggo two-way inbox`.

