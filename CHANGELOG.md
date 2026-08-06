# Changelog

All notable changes to this skill. Versions follow the `VERSION` file, which
must match `package.json`.

## 1.4.8

A blind evaluation scored 19/20 with the miss on the CI supply-chain fixture:
the reviewer found every problem in it — floating action tags, `npm install`
over `npm ci`, an audit threshold below `high` — and rated the lot **low**. That
was a gap in this skill's guidance, not in the reviewer.

### Changed

- **`references/supply-chain.md` now says what the attack costs.** It was
  thorough on *what* to fix and silent on *what happens when you don't* — the
  only reference shaped that way, and it read as hygiene as a result. It now
  opens with the concrete chain: a mutable tag is a pointer, whoever compromises
  the upstream repo re-aims it, and the code then runs in your job with your
  job's `env` — where the deploy credentials already are. No exploit to write.
- **Severity calibration table** added, keyed on what the compromised step can
  reach: High when the job holds deploy credentials, signing keys, or publish
  rights; Medium when it holds nothing meaningful. Long-lived cloud credentials
  in CI where OIDC exists are High.
- **Watchlist item 20 in `SKILL.md`** carries the same framing, since the
  watchlist stays in context when the reference is not loaded.

### Result

Re-running the blind evaluation against the same corpus with a fresh reviewer
moved that finding from one **low** to a **high** (mutable tags plus long-lived
AWS keys, which the earlier run missed entirely) plus a **medium** (`npm
install`, weak audit threshold). Recall 20/20, precision 6/6, no false positives
on the six secure files.

## 1.4.7

Acts on what the first blind evaluation exposed. The 20/20 recall result was
real, but it showed the corpus could no longer teach us anything: it measured
only whether vulnerabilities were found, never whether correct code was left
alone.

### Added

- **`tests/clean/`** — six secure counterparts (scoped queries, env-sourced
  config, parameterized SQL with argv subprocess, argon2id, fully verified JWT,
  hardened upload). A finding of medium or above against any of them is a false
  positive and fails the eval. Low-severity hardening nits are tolerated.
  Without this the corpus rewarded flagging everything.
- **`eval_skill.py --blind DIR`** makes the blind protocol reproducible instead
  of hand-rolled: it copies the whole corpus to `module_NN.<ext>` in
  hash-shuffled order — so neither the filename nor the position hints at the
  answer — and writes a translation map. `--grade --map` translates back.
  Filenames like `w05_jwt_verification.js`, and the `fixtures/` vs `clean/`
  split, both gave the answer away otherwise.
- Grading now reports **precision** alongside recall, and the audit prompt warns
  that some files are secure and padding counts against you.

### Fixed

- **`w02_hardcoded_secrets.py` contradicted itself.** Its comment claimed the
  values were placeholders while `DB_PASSWORD = "prod_admin_2024!"` was not
  placeholder-shaped. The blind reviewer caught the inconsistency and flagged it
  as a real credential rather than trusting the comment — correctly. All four
  values are now unambiguously placeholders.

## 1.4.6

### Fixed

- **A quiet refresh no longer produces a commit.** `refresh.py` stamped a fresh
  `last_run` into `_sources/_state.json` on every run, so a week where nothing
  changed upstream still produced a diff: a pull request every Monday forever,
  and a commit that pushed `main` one ahead of the last release tag for no
  reason. It now rewrites `_state.json` and `CHANGES.md` only when the upstream
  content or the fetch-error list actually changed.

  To keep `check_skill.py`'s 30-day staleness gate meaningful through a
  genuinely quiet stretch — where silence is otherwise indistinguishable from a
  broken pipeline — the timestamp is still refreshed on a heartbeat every
  `REFRESH_HEARTBEAT_DAYS` (default 20, deliberately 10 days inside the gate).

## 1.4.5

Documentation sweep across every doc in the repository, verified against the
code rather than written from memory.

### Changed

- **README** gains a Continuous Integration section: all four workflows in one
  table with their triggers, what they do, and whether each needs a credential
  (three of four do not), plus the invariants `check_skill.py` enforces on them.
- **`scripts/README.md`** gains a script index table, and its workflow list now
  includes the bounds check and the no-credential brief path.
- **`tests/README.md`** documents how to add a fixture and why fixtures must
  never use a real provider key format — the mistake that once got the
  repository blocked by push protection.
- **`_sources/README.md`** documents everything the pipeline now writes there:
  `_state.json`, `CHANGES.md`, `CURATION.md`, `briefs/`, and cache pruning.
- **`SKILL.md`**, **`AGENTS.md`** and **`GEMINI.md`** clarify that
  `$secure-webapp maintain` runs from a clone of the source repository, not an
  installed copy — matching the skip behaviour added in 1.4.3.

Verified mechanically: all TOC anchors resolve, every file path referenced in
backticks exists, all 20 documented command invocations run and every flag they
use is accepted, and the packaging list matches the built archive exactly.

## 1.4.4

Closes the Codex/Gemini gaps. End users on those agents were already fully
supported — verified by installing for both and inspecting the discovery blocks
— but two things assumed Claude.

### Fixed

- **Codex and Gemini users were getting a stale trigger list.** The installers
  embed their own copy of the "when to use this skill" text in the
  `AGENTS.md` / `GEMINI.md` discovery block, and it was never updated when AI/LLM
  coverage landed in 1.4.0. Those users' agents were therefore *less* likely to
  fire the skill on prompt-injection or agent-tool work — precisely the users
  most likely to need it. All three installers now match `SKILL.md`, and
  `check_skill.py` fails the build if the four copies drift again.

### Added

- **`curate_references.py --write-briefs`** renders one self-contained curation
  brief per in-scope reference — instructions, current reference, upstream diff,
  and full changed source text — with no API call. Hand a brief to Codex, Gemini
  CLI, or any other agent, apply its edits, then run `verify_agent_changes.py`,
  which is agent-agnostic already. Briefs are gitignored and `_sources/` never
  ships, so they cannot leak into the package.

## 1.4.3

Adds the agent variant of reference curation, deliberately kept off the schedule.

### Added

- **`.github/workflows/curate-agent.yml`** — runs Claude Code with real
  repository access to curate references. `workflow_dispatch` only, for the rare
  structural upstream change (a new Top 10 edition, an ASVS major version) where
  the single-turn scripted path cannot read whole documents or reason across
  several references. It refreshes, validates a baseline, curates, verifies, and
  opens a PR.
- **`scripts/verify_agent_changes.py`** — re-establishes after the fact the
  boundary the scripted path holds by construction. Fails the run, so no PR is
  opened, if anything outside `references/` changed, if nothing changed, or if
  the tree stops validating. `SKILL.md`, `scripts/`, `.github/`, `bin/`,
  `agents/`, `VERSION`, `package.json`, the archive and `SHA256SUMS` are refused
  even when the allowlist is widened. Useful by hand after any agent-assisted
  editing session.
- `check_skill.py` fails the build if the agent workflow ever gains a `schedule:`
  trigger, loses its `workflow_dispatch` trigger, drops the bounds check, or
  gains auto-merge.

### Fixed

- **Validators no longer fail confusingly in an installed copy.** `check_skill.py`
  ships in the archive but validates a *source tree*, so running it from
  `~/.claude/skills/secure-webapp` — which `$secure-webapp maintain` invites —
  died on `missing required path: .gitignore`, a file the package deliberately
  excludes. It predates this release; the `tests/` requirements added in 1.4.0
  widened it. Both `check_skill.py` and `eval_skill.py --check` now detect an
  installed copy and skip with an explanation instead of a spurious failure.

## 1.4.2

Sharpens reference curation, after asking whether it should instead run as an
agent with repo write access in CI. It should not — the guardrails only hold
because the model never touches the filesystem — but the question exposed a real
gap in how little context the model was given.

### Changed

- **Curation now sees enough to judge.** The model previously got the reference
  plus a 3-line-context diff, which is rarely enough to tell whether guidance
  actually shifted. It now receives 25 lines of context, the full current text of
  each changed upstream file where size allows, and the names of sibling
  references grounded in the same sources so it does not pull their subject
  matter into the file it is editing. In testing, prompt context went from ~11k
  to ~27–37k characters.

### Added

- **Structural guardrails on proposals.** Unbalanced code fences, a collapsed
  section structure, links to a reference that does not exist, and
  credential-shaped strings are now rejected alongside the existing checks.
- **Validation at both ends.** The repository must validate before any edit — if
  it does not, the run refuses and spends zero model calls, since otherwise an
  unrelated pre-existing failure would revert perfectly good edits. After
  editing, the validator runs again and every edit from the run is reverted on
  failure.
- `--print-prompt` renders the exact prompt for the first in-scope reference
  without calling the API, so what gets sent is inspectable and testable.

## 1.4.1

Supply-chain and build-integrity follow-ups found while merging the Dependabot
action bumps.

### Fixed

- **CI was pinned to an untagged upstream commit.** `actions/checkout` had been
  pinned to `4f1f4ae`, a commit on the action's default branch six commits past
  `v7.0.0` and belonging to no release. That is not a Dependabot fault: bare SHA
  pins with no version comment give it nothing to match releases against, so it
  follows the branch head. All five action pins are now tagged releases with a
  `# vX.Y.Z` comment — `actions/checkout` moves to `v7.0.1` (a release, and
  newer than the untagged commit it replaces).
- **Builds are now reproducible.** `package_skill.py` stamped each zip entry
  with the file's mtime and a umask-dependent mode, so an unchanged tree
  produced a different archive hash on every build. `SHA256SUMS` churned on
  no-op refreshes and "did the artifact actually change?" was unanswerable. All
  entries now use a fixed 1980-01-01 timestamp and explicit modes; the same tree
  yields a byte-identical archive.

### Added

- `check_skill.py` fails the build if any workflow uses an action that is not
  pinned to a full 40-character SHA **and** annotated with its release version.
- `validate.yml` rebuilds the archive after touching sources and fails if the
  hash changes, so the reproducibility guarantee is enforced rather than assumed.

## 1.4.0

The weekly OWASP refresh had been failing every Monday since 6 July 2026, and
the reference sync it fed had never propagated a guidance change. This release
repairs the pipeline, replaces the sync with something that works from real
diffs, and adds the first tests of what the skill actually detects.

### Fixed

- **Refresh pipeline repaired.** `JSON_Web_Token_for_Java_Cheat_Sheet.md` was
  renamed upstream to `JSON_Web_Token_Cheat_Sheet.md`; the resulting 404 exited
  `refresh.py` non-zero and killed the workflow at its first step, leaving the
  cache frozen for five weeks with nothing going red. `refresh.py` now exits 0 on
  partial fetch failures — the cached copy is kept and the failure is reported —
  and non-zero only when a whole source returns nothing, or under the new
  `--strict`. Fetch errors always print, even under `--quiet`.
- **Stale caches now fail the build.** `check_skill.py` fails if the upstream
  cache is older than 30 days (`SKILL_MAX_SOURCE_AGE_DAYS`), so a broken refresh
  surfaces in normal CI instead of a scheduled workflow nobody reads. The
  refresh workflow also opens or updates a maintenance issue naming any file it
  could not fetch.
- **Installer parity.** `bin/install.js` omitted `scripts/`, so `npx` installs
  lacked the files `$secure-webapp maintain` and `setup-auto-update.js` depend
  on — while the README claimed it copied every skill file. It now installs the
  same set as the released archive, and `check_skill.py` fails if the two
  diverge. `LICENSE` (MIT) now ships alongside `LICENSE.txt` (OWASP attribution).
- **Validator drift.** `check_skill.py` enforced a hardcoded five-mode list and
  had never learned about `report`, `remediate`, or `update`. Modes are now
  parsed from `SKILL.md` and cross-checked against all three installers,
  `AGENTS.md`, `GEMINI.md`, and `README.md`.
- **Stale cache entries** are pruned when the manifest stops tracking a file, so
  an upstream rename cannot leave a copy behind pretending to be current.

### Added

- **`references/ai-and-llm.md`.** Three AI cheat sheets were already being
  downloaded with zero coverage in the skill. Covers prompt injection (direct
  and indirect), authorizing agent tool calls against the end user rather than
  the service account, model output as an untrusted sink, RAG and memory
  scoping, and MCP server trust. Adds a routing row, watchlist items 17–19, and
  audit-checklist category 12. Also tracks the Secure Coding with AI cheat sheet.
- **`scripts/curate_references.py`.** Reads the diff of what moved upstream and
  proposes targeted reference edits for human review. Guardrails reject
  proposals that drop the title, fall below 75% of original length, reintroduce
  the removed generated-section marker, or are no-ops; rationales are written
  into the pull request body. Requires `ANTHROPIC_API_KEY`; without it the
  refresh path is unchanged.
- **`scripts/reference_map.json`.** Declares which upstream sources ground which
  reference. Validated in both directions against `manifest.json`.
- **Detection corpus (`tests/`).** One deliberately vulnerable fixture per
  watchlist item, plus `scripts/eval_skill.py`: `--check` is a CI gate that
  fails if a watchlist item has no fixture, and `--prompt`/`--grade` run and
  score a real audit, reporting per-fixture PASS/UNDER/MISS and recall.
- **Installer integrity verification.** `install.sh` and `install.ps1` verify the
  downloaded archive against the release's `SHA256SUMS` and fail closed on
  mismatch, missing sums, or no available hashing tool. `--no-verify` /
  `-NoVerify` override.

### Changed

- **Refresh pull requests no longer auto-merge.** Upstream OWASP content — or a
  model's reading of it — reaching a shipped artifact without review is a
  supply-chain path this repository now closes. `check_skill.py` fails the build
  if auto-merge returns, or if the workflow commits `references/` without having
  run the curation step.

### Removed

- **`scripts/sync_references.py`.** Its generated section was a fixed bullet list
  behind substring checks that were always true. Across twelve refreshes it
  touched `references/` exactly twice: once to insert itself, and once to delete
  a blank line. The other ten produced nothing. The generated section is
  stripped from all references, and the docs no longer claim references sync
  automatically.

## 1.3.1 and earlier

See the git history and GitHub releases.
