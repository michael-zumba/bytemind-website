# ByteProof — Technical Review & Improvement Roadmap

**Reviewed version:** 1.5.6 (`91c624e`)
**Review date:** 2026-08-12
**Scope:** desktop app (`src/`), Word/generic editing integrations, licensing &
activation (`server/`, `src/licensing.py`, `src/activation.py`, `src/polar.py`),
local AI engine (`src/local_model.py`), build/distribution tooling, training
pipeline, and the existing test suite.

---

## 1. Executive summary

ByteProof is in genuinely good shape for a v1.5 desktop product. The codebase
already contains a lot of careful safety engineering that most comparable apps
skip: citation/math/field-code protection, diff-based tracked-changes
application, selection-moved guards, similarity checks, cancellation,
checksum-verified model downloads, trial hardening across two storage
locations, and a reasonable offline smoke suite (70+ checks pass).

No rewrite is needed. The improvements that matter most are:

1. **Fix a real silent-failure bug** in Word auto-apply (and the usage
   accounting tied to it).
2. **Stop storing users' API keys in plaintext** settings JSON.
3. **Harden supply chain and distribution**: verify the downloaded llama.cpp
   runtime and update installers, and sign/notarize macOS and Windows builds.
4. **Handle long selections properly** (chunking + progress), since the local
   engine is capped at an 8k context and cloud providers have output limits.
5. **Retire the legacy Stripe/email licensing path** now that Polar is the
   canonical owner, or move its registry to durable storage if it is kept.

Everything else is UX depth and architecture hygiene that can be phased in
without risk.

---

## 2. How this review was done

- Read every module in `src/`, `server/`, `config/`, `training/`, `tests/`,
  prompts, build scripts, GitHub Actions workflow, and release docs.
- Ran the full offline smoke suite:
  `QT_QPA_PLATFORM=offscreen ./venv/bin/python tests/test_smoke.py`
  → `ALL_SMOKE_TESTS_PASSED`.
- Ran `ruff check`: 9 findings, all minor (unused imports, timezone-naive
  datetimes), mostly inside the private `tools/` folder.
- Pyright config exists, but Pyright is not installed in the project venv, so
  type checking was not re-run here.
- OpenAI official docs returned HTTP 403 from this environment, so the
  recommended OpenAI model default is flagged for verification during
  implementation rather than asserted here.

---

## 3. What is already strong

### Core editing safety
- Protected spans for Word field codes, LaTeX, math/Unicode ranges, and
  embedded objects (`src/logic.py` `_find_protected_spans`,
  `protect_special_chars`).
- Diff-based application with reverse-order edits, so indices stay valid
  (`apply_corrections_with_diff`).
- Missing/empty corrected segments fall back to the original text — user text
  can never be deleted by a malformed model response.
- Similarity guard: corrections below 0.30 similarity are never auto-applied;
  low-similarity results require explicit review.
- Selection-moved verification before applying (Word and generic apps).
- Conversational-refusal detection with one retry before showing output.
- Cancellation via double-Esc for proofreads, downloads, and local server
  startup.

### Local AI engine
- Resumable downloads, SHA-256 verification, disk-space checks, storage
  budget, automatic model cleanup, and a pinned llama.cpp release.
- Hardware-aware model recommendation (RAM + Apple Silicon detection).
- Local-only free tier preserved after trial expiry (3 proofreads/day).

### Licensing
- Polar is the canonical licensing owner with server-side device limits.
- Local license data is mirrored into the OS credential store; stored license
  payloads are re-validated (signature + machine fingerprint) on every load.
- Trial start is stored in two locations so deleting one cannot reset it.
- Deactivation frees a device slot; activation deep-link scheme
  (`byteproof://`) works on both platforms.

### Product/UX groundwork
- Global hotkeys with permission retry and clear macOS guidance.
- Frontmost-app capture at hotkey press + background-app history/probing so
  button/tray-initiated proofreading still finds the source app.
- Generic editing verifies the selection before pasting and verifies the
  result after pasting.
- Dynamic-island style status pill, tray menu, capture diagnostics, support
  folder access, update checks, and free-tier status on the main button.
- Settings UI is modern: sidebar tabs, provider cards, badges, test-connection
  buttons, local model management with progress.

### Engineering hygiene
- Reasonable module boundaries for a desktop app, with platform adapters for
  Word and generic editing.
- Offline smoke tests cover licensing, trial logic, providers, diff safety,
  GUI construction, hotkey conversion, downloads, and more.
- Version bump tooling updates `APP_VERSION`, Windows metadata, and the
  website update feed together.
- Clear build guides for macOS (ARM/Intel) and Windows.
- A real fine-tuning pipeline exists for future ByteProof-tuned GGUFs.

---

## 4. Critical findings

### 4.1 High — Word auto-apply can silently fail, yet report success

In `proofread_selection_once`, the return value of `apply_corrections_with_diff`
is ignored (`src/logic.py:1141`), and the function unconditionally sets
`result_status = "Proofreading complete."` (`src/logic.py:1146`).

`apply_corrections_with_diff` returns `False` when:
- the selection moved more than 10 characters, or
- any Word range operation throws.

On Windows, `WindowsWordIntegration` methods also swallow exceptions with
`print(...)` and return `None` (`src/word_integration.py`), so failures are
invisible. The user is told the proofread completed, the diff panel may show
changes, but nothing was applied.

Worse, `_proofread_consumes_usage` treats `"Proofreading complete."` as a
successful proofread, so a free-tier user can burn one of three daily credits
on a run that did nothing.

**Fix direction:**
- Make `apply_corrections_with_diff` propagate a clear failure result.
- Have Word platform methods raise (or return success booleans) instead of
  swallowing errors.
- Only record usage after a confirmed apply (or a deliberate user-approved
  REVIEW_NEEDED apply).
- Show a distinct error toast/status ("Could not apply — the selection moved
  in Word. Reselect and try again.").

### 4.2 High — Cloud API keys are stored in plaintext

Provider API keys are written directly into `settings.json`
(`src/settings.py:313-323`). On macOS this is
`~/Library/Application Support/ByteMind/ByteProof/settings.json`; on Windows,
`%APPDATA%\ByteMind\ByteProof\settings.json`.

The licensing code already has an OS-credential-store pattern
(`_secure_store_set/_get/_delete` in `src/licensing.py`); the same approach
should be applied to API keys (or use `keyring`), with settings.json holding
only masked labels/pointers.

**Fix direction:**
- Add `api_keys` to the macOS Keychain / Windows Credential Manager.
- Migrate existing plaintext keys once on upgrade (read old file, store
  securely, scrub from JSON).
- Keep the "up to 5 keys" UI but load/save through the secure store.

### 4.3 High — Supply chain and update integrity gaps

The llama.cpp runtime is downloaded from GitHub and executed, but is **not**
checksum-verified (`ensure_runtime` in `src/local_model.py:470`), unlike the
model GGUFs, which are SHA-256 verified. A compromised or tampered GitHub
release (or MITM) would mean executing an unverified binary.

Update installers are also downloaded and opened without verifying a checksum
or signature (`src/app_version.py` `download_update`).

The GitHub Actions release workflow builds macOS DMGs without Apple
notarization and Windows builds without code signing, so users will see
Gatekeeper/SmartScreen warnings (the self-signed certificate only preserves
Accessibility permissions; it is not a trust anchor for distribution).

**Fix direction:**
- Pin and verify SHA-256 for each llama.cpp platform asset (in code or a
  signed manifest).
- Add `sha256` fields to `byteproof-version.json` and verify before opening
  installers.
- Sign with Apple Developer ID + notarize in CI; sign Windows binaries (e.g.,
  Azure Trusted Signing) or at minimum document the warning UX.

### 4.4 High — No long-selection strategy

The local server starts with `--ctx-size 8192` (`src/local_model.py`
`LocalModelServer.start`). Cloud providers have per-provider output caps, and
the app sends the whole selection in one request. Long selections (whole
thesis chapters, long email threads) will either hit context limits, produce
truncated output, or fail.

**Fix direction:**
- Estimate tokens before sending; warn or reject over-budget selections.
- Chunk long text by paragraphs with overlap and process sequentially,
  reporting progress per chunk.
- Consider scaling `--ctx-size` based on RAM for local models.
- Preserve Word diff semantics across chunks (apply chunk edits with offsets
  computed on the original text).

### 4.5 Medium — Legacy Stripe/email licensing is still alive

Polar is configured and canonical (`POLAR_ORGANIZATION_ID` is set in
`src/settings.py`), but the legacy email + Stripe path remains fully present:
- `src/activation.py` still points at `byteproof-api.onrender.com`.
- `server/` (FastAPI + Stripe webhook + license registry) is still deployable
  and documented as the activation flow.
- `STRIPE_PAYMENT_URL` is still referenced in `src/gui.py` as the fallback
  purchase URL.

The legacy server's Render blueprint uses the free plan, which has a
non-persistent filesystem (`server/README.md` explicitly warns the payment and
license registries reset on redeploy). That is a data-loss risk if it is kept
as anything other than a dev sandbox.

**Fix direction:**
- Decide: retire legacy entirely (recommended), or keep it only behind an
  explicit env flag for pre-Polar buyers.
- If kept, move the registry to Postgres and add rate limiting.
- Remove dead constants (`STRIPE_PAYMENT_URL`, legacy URLs) and update docs
  once retired.

### 4.6 Medium — macOS Word comment insertion is brittle

`MacOSWordIntegration.add_comment` inserts comments by copying text to the
clipboard, then using System Events to click the `Insert → Comment` menu item
or send keyboard shortcuts (`src/word_integration.py`
`_trigger_comment_and_paste`). This is fragile across Word versions,
localizations, and ribbon configurations.

**Fix direction:**
- Investigate Word for Mac's native AppleScript dictionary for a comment API.
- If UI scripting must stay, add localization-tolerant menu matching
  (multiple menu labels), verify the comment actually appears, and report a
  clear error if every method fails.

### 4.7 Medium — Diagnostics can capture private text

`_debug_log` writes selection previews (first 40 characters) and app names to
`capture.log` (`src/generic_editing.py`). `print()` statements throughout also
carry text lengths and API error bodies. For a privacy-first product, log
content should be redacted and diagnostics should be opt-in.

**Fix direction:**
- Centralize logging with redaction (keys, selected text beyond short safe
  snippets, emails unless needed for support).
- Truncate/rotate logs (already partially handled by `cache_cleanup.py`).
- Add a "share diagnostics" flow that lets users review what is being sent.

---

## 5. UI/UX review

### What already works well
- The floating status pill is a strong pattern: it keeps the user in their
  document while showing progress, elapsed time, and result state.
- Frontmost-app capture at hotkey press and background-app history is
  thoughtful — this is the hard part of "proofread anywhere" and it is solved
  well.
- Permission flows (Accessibility) are clear, with actionable dialogs and
  retry logic.
- Tray menu, hotkey hints, and the "Free mode — N left today" button are
  useful micro-UX.
- Settings uses a clean sidebar + cards + badges pattern and surfaces the
  right choices without a wall of controls.

### Recommended UX improvements

#### 5.1 Staged progress and streaming
Today the pill shows "Preparing local AI…" / "Proofreading…" and a timer, but
the user does not know what stage the task is in. Add explicit stages:
"Reading selection…", "Generating reviewer comment…", "Proofreading
paragraph 2 of 5…", "Applying changes…". For cloud providers, stream the
response so the diff appears progressively (or at least show token/char
progress).

#### 5.2 Diff review depth
The "Proposed Changes" panel is a single text area with colored
strikethrough/insertions. For a tool whose core promise is *safe* edits:
- Add change statistics (`+12 / −5 words`), not just corrected word count.
- Add next/previous change navigation and per-change accept/reject (at least
  in the review panel; Word's own tracked changes can remain the source of
  truth there).
- Offer a plain/side-by-side toggle.
- After auto-apply in a generic app, show "Press Cmd/Ctrl+Z to undo" in the
  success toast.

#### 5.3 Per-mode auto-apply
One global `auto_apply` checkbox governs both Word and every other app. These
are very different risk profiles: Word has tracked changes (safe), while an
email draft or chat window is replaced in place (riskier). Offer separate
settings — e.g., "Auto-apply in Word" and "Auto-replace in other apps" — and
consider defaulting non-Word apps to preview mode.

#### 5.4 Custom instructions
The prompt layer already supports `user_instructions`, but no UI exposes it.
Add an "Additional instructions" field in General settings (e.g., "never
change British terminology", "keep 'whilst'", "don't touch equations").

#### 5.5 First-run onboarding
The welcome modal ("local AI is ready to download") is functional but generic.
Replace with a first-run card in the main window: what ByteProof does, the
recommended local model, a one-click download button, and the hotkey list.
Keep it dismissible and avoid blocking the window.

#### 5.6 Privacy transparency
When the user selects a cloud provider, show a short note: "Selected text will
be sent to <provider>. The local AI model keeps everything on your computer."
Link to a privacy page. This is a differentiator for academic users.

#### 5.7 Status surface on the main window
Show the active provider + model + remaining free credits directly in the
status bar, so users do not have to open Settings to understand why output
quality or speed changed.

#### 5.8 Accessibility and theming
- Dark mode (system-following), at least for the main window and settings.
- Check contrast ratios and font scaling at macOS/Windows accessibility sizes.
- Ensure all primary actions are reachable by keyboard (the diff panel Apply
  already has Cmd+Return, which is good).
- Localization hooks: the app is currently English-only; keep strings in one
  place if other languages are planned.

#### 5.9 Empty/edge states
Polish messages for: no model downloaded yet, no internet, provider rate
limit, local engine failed to start, and very long selections. Today many of
these work, but they surface as raw error strings from API calls.

---

## 6. Core function optimisation

### 6.1 Chunking and context management (top priority)
As noted in 4.4, add a text-processing pipeline:
- Token/char estimation before the request.
- Paragraph-level chunking with overlap and per-chunk offsets.
- Sequential processing with cancellation and progress.
- Reassembly that preserves protected spans and paragraph boundaries.
- Per-chunk similarity checks before applying.

### 6.2 Provider layer cleanup
- Replace string-matching retry logic with typed/structured errors.
- Add per-provider timeouts, streaming, and usage estimates (approximate token
  counts shown before sending).
- Version provider defaults remotely (a small `byteproof-providers.json`
  feed, like the local model manifest) so model names can be refreshed
  without shipping a new app build.
- Refresh current defaults: OpenAI's `gpt-4o` and Anthropic's
  `claude-sonnet-4-20250514` are stale as of this review; verify the current
  recommended models against official docs (OpenAI docs were 403 here) and
  pick defaults that balance quality, latency, and cost for proofreading.

### 6.3 Post-processing guards
The prompts ban em dashes and Markdown, but nothing enforces it
deterministically. Add cheap post-filters:
- Replace em dashes with commas/parentheses/periods per prompt rules.
- Strip markdown artifacts (`**`, backticks, `#`).
- Re-run citation/field-code protection after correction (already done for
  special chars; make it a single guaranteed post-pass).

### 6.4 Local engine lifecycle
- Add an idle timeout so the llama.cpp server does not keep 2–9 GB of RAM
  resident after, say, 30 minutes of inactivity (with a user setting).
- Consider pre-warming the local server at launch only if a model is already
  installed and the user enables it.
- Surface llama server logs in a user-friendly way when startup fails.

### 6.5 Evaluation and model quality
- Wire the training pipeline into a repeatable eval: run `eval_grammar.py`
  against a fixed academic test set before every model catalog update.
- Enable a *signed* remote model manifest so future ByteProof-tuned GGUFs can
  be delivered without app releases (the plumbing already exists, gated off).
- Track per-provider output quality manually or via opt-in feedback (thumbs
  up/down on results) to guide default model choices.

### 6.6 Word integration
- Prefer native Word APIs over clipboard/UI scripting where possible,
  especially for comments on macOS.
- Consider processing table cells individually instead of skipping table
  selections entirely.
- Add a post-apply verification in Word: compare a small range around each
  edit, or at least confirm the document text changed, before reporting
  success.

---

## 7. Architecture & code health

### 7.1 Modularize the GUI
`src/gui.py` is ~5,200 lines and mixes workers, the settings dialog, the main
window, theme, and platform workarounds. Split into:
- `src/ui/workers.py`
- `src/ui/settings_dialog.py`
- `src/ui/main_window.py`
- `src/ui/widgets.py` (pill, diff panel)

Do this incrementally (move workers first — they are self-contained), not as a
big-bang refactor.

### 7.2 Split `logic.py`
`src/logic.py` (~1,300 lines) mixes prompts, provider clients, diff
application, and Word orchestration. Suggested split:
- `src/providers/` — request building, retries, streaming, errors.
- `src/prompts.py` — prompt loading and style/context assembly.
- `src/editing/` — diff engine, protected spans, chunking, reassembly.
- `src/word/` — platform adapters (already mostly isolated).

### 7.3 Logging
Replace scattered `print()` with a small logging module (rotating file,
redaction, debug levels). Keep the existing support-folder paths so current
diagnostics flows keep working.

### 7.4 Config robustness
- Write `settings.json` atomically (temp file + `os.replace`) to avoid
  corruption on crash.
- Validate settings with a schema on load (lightweight dataclass/pydantic
  model), and keep the existing migration logic.

### 7.5 CI quality gates
- Run the offline smoke suite, `ruff`, and `pyright` on every PR.
- Add a release job that runs tests before building installers.
- Add checksum generation and injection into the version feed as part of the
  release process.

### 7.6 Dependency hygiene
- Move `pyinstaller` out of runtime `requirements.txt` into a dev-requirements
  file.
- Remove dead/legacy code: `config/deepseek_config.py` OpenAI-client helpers
  (the app talks HTTP directly), `STRIPE_PAYMENT_URL` after Polar-only
  migration, legacy server endpoints after retirement.
- Move the hard-coded keychain password in `tools/sign_byteproof.sh` to an env
  var or Keychain lookup.

### 7.7 Documentation
- Update `README.md` / `BYTEMIND_SETUP.md` once the legacy licensing path is
  retired, so operators do not deploy the old server by mistake.
- Keep the version-feed and signing docs in sync with the CI pipeline.

---

## 8. Roadmap

Phases are ordered so that correctness and trust land first, then UX depth,
then architecture. Each phase is independently shippable and ends with a
version bump (the release process already exists).

### Phase 0 — Stabilize (1–2 weeks)
**Goal:** no silent failures, no plaintext credentials, regression protection.

- Fix the silent Word apply failure and usage accounting (4.1).
- Store API keys in the OS credential store with migration (4.2).
- Atomic settings writes + settings schema validation (7.4).
- Add a CI job running smoke tests + `ruff` + `pyright` (7.5).
- Add regression tests for the apply-failure paths (selection moved, Word
  throws, Windows COM failure).

**Verification:** smoke suite green; manual test of Word apply with selection
changed mid-run; credentials file contains no keys; CI green.

### Phase 1 — Trust & distribution (1–2 weeks)
**Goal:** verified downloads, signed builds, one licensing path.

- Add SHA-256 verification for the llama.cpp runtime and update installers
  (4.3).
- Add macOS notarization and Windows signing to CI (4.3).
- Retire legacy Stripe/email activation (4.5) or move its registry to
  Postgres with rate limiting.
- Add log redaction + opt-in diagnostics (4.7).
- Add the cloud-provider privacy notice (5.6).

**Verification:** clean installs of signed builds on a fresh macOS/Windows
machine; tampered runtime/installer rejected; legacy endpoints decommissioned
or persistent.

### Phase 2 — Long text & performance (2–3 weeks)
**Goal:** proofread long selections reliably and with visible progress.

- Token estimation + chunking pipeline with paragraph overlap (6.1).
- Staged progress in the pill (5.1); streaming for cloud providers.
- Local server idle timeout + smarter context sizing (6.4).
- Per-chunk similarity and protected-span checks.

**Verification:** a 5,000-word thesis chapter proofreads successfully in Word
and in a generic app; progress updates appear per chunk; cancel works
mid-chunk.

### Phase 3 — UX depth (3–5 weeks)
**Goal:** users can trust and control the result.

- Diff panel upgrade: stats, navigation, plain/side-by-side, undo hint
  (5.2).
- Separate auto-apply controls for Word vs other apps, with preview default
  for riskier apps (5.3).
- Custom instructions field (5.4).
- First-run onboarding card (5.5).
- Active provider/model + remaining credits in the status bar (5.7).
- Dark mode and accessibility pass (5.8).
- Edge-state copy polish (5.9).

**Verification:** usability walkthroughs with 2–3 real users (or yourself in
the three core flows: Word tracked changes, email draft, code editor);
keyboard-only pass; contrast check.

### Phase 4 — Architecture & quality (ongoing, 3–5 weeks)
**Goal:** maintainable codebase that supports future features.

- Modularize `gui.py` and `logic.py` (7.1, 7.2).
- Centralized logging (7.3).
- Remote provider/model defaults feed + default model refresh (6.2).
- Eval harness + signed remote model manifest (6.5).
- Word comment insertion hardening (6.6).
- Dev-dependency separation and dead-code removal (7.6).

**Verification:** all existing tests pass after each refactor slice; packaged
app behaves identically; Pyright 0 errors; ruff clean.

### Phase 5 — Growth (optional)
Ideas to evaluate only after 0–4 are solid:
- Opt-in anonymous usage analytics and result feedback (thumbs up/down).
- Managed cloud/credits option for users who do not want to manage local
  models or keys.
- Batch proofreading (whole document, multiple selections).
- Per-document settings (spelling variant, style, custom glossary).
- Team licensing / multi-seat management via Polar.

---

## 9. Decisions needed from you

1. **Legacy licensing:** retire the Stripe/email server entirely, or keep it
   as a gated fallback with durable storage? (Recommend: retire; Polar is
   live and the app already routes to it.)
2. **Non-Word auto-apply:** keep the current replace-in-place default, or
   default to preview for email/chat apps with per-app rules?
3. **Telemetry/feedback:** is opt-in usage analytics + result feedback
   acceptable for future model decisions?
4. **Distribution budget:** are you willing to get an Apple Developer account
   (and optionally Windows signing) so CI can produce trusted installers?
5. **Theming:** is dark mode a priority for your audience, or is the current
   light theme sufficient for the first roadmap cycle?
6. **Custom instructions:** are there specific authoring rules (terminology,
   style, citations) that should be built-in presets rather than free text?

---

## 10. Findings register

| # | Area | Severity | Where | Recommendation |
|---|------|----------|-------|----------------|
| 1 | Word apply | High | `src/logic.py:1141-1146`, `src/word_integration.py` | Propagate failure; report accurately; don't count usage on failure |
| 2 | Credentials | High | `src/settings.py:313-323` | Store API keys in OS credential store; migrate existing |
| 3 | Supply chain | High | `src/local_model.py:470`, `src/app_version.py` | Verify runtime + installer checksums; sign/notarize builds |
| 4 | Long text | High | `src/local_model.py` (ctx 8192), `src/logic.py` | Chunking, token estimation, progress, per-chunk safety |
| 5 | Licensing | Medium | `src/activation.py`, `server/`, `src/settings.py` | Retire legacy path or use durable registry + rate limits |
| 6 | Word comments | Medium | `src/word_integration.py` | Native API or localization-tolerant UI scripting + verification |
| 7 | Privacy | Medium | `src/generic_editing.py` logs | Redact logs; opt-in diagnostics; cloud provider notice |
| 8 | UX progress | Medium | `src/gui.py` workers/pill | Staged progress; streaming |
| 9 | Diff UX | Medium | `src/gui.py` diff panel | Stats, navigation, side-by-side, undo hint |
| 10 | Auto-apply | Medium | `src/settings.py`, `src/gui.py` | Per-mode controls; preview default for non-Word |
| 11 | GUI monolith | Low/Medium | `src/gui.py` (~5.2k lines) | Incremental module split |
| 12 | Logic monolith | Low/Medium | `src/logic.py` (~1.3k lines) | Split providers/prompts/editing |
| 13 | Logging | Low/Medium | all `src/` | Central logger with rotation + redaction |
| 14 | Settings writes | Low | `src/settings.py` | Atomic writes + schema validation |
| 15 | CI | Low/Medium | `.github/workflows/build-release.yml` | Tests/lint/type-check gate; signing + checksums |
| 16 | Dead code | Low | `config/deepseek_config.py`, `STRIPE_PAYMENT_URL` | Remove after licensing cleanup |
| 17 | Provider defaults | Low | `src/settings.py` | Remote defaults feed; verify current model IDs |
| 18 | Local engine lifecycle | Low/Medium | `src/local_model.py` | Idle timeout, smarter ctx, friendly startup errors |
| 19 | Build tooling | Low | `tools/sign_byteproof.sh` | Keychain password via env; Windows signing docs |
| 20 | Model quality | Medium | `training/` | Repeatable eval; signed manifest; own fine-tune |

