# Changelog

All notable changes to this skill. Versions follow the `VERSION` file, which
must match `package.json`.

## 1.4.0

The weekly OWASP refresh had been failing every Monday since 8 June 2026, and
the reference sync it fed had never propagated a guidance change. This release
repairs the pipeline, replaces the sync with something that works from real
diffs, and adds the first tests of what the skill actually detects.

### Fixed

- **Refresh pipeline repaired.** `JSON_Web_Token_for_Java_Cheat_Sheet.md` was
  renamed upstream to `JSON_Web_Token_Cheat_Sheet.md`; the resulting 404 exited
  `refresh.py` non-zero and killed the workflow at its first step, leaving the
  cache frozen for 72 days with nothing going red. `refresh.py` now exits 0 on
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
  behind substring checks that were always true. Across eight refreshes it
  produced exactly one change to `references/`: a deleted blank line. The
  generated section is stripped from all references, and the docs no longer
  claim references sync automatically.

## 1.3.1 and earlier

See the git history and GitHub releases.
