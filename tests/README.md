# Detection corpus

`check_skill.py` proves the package has the right *shape*. This directory proves
it has the right *effect*: that the skill still finds what its Always-On
Watchlist says it finds.

- `fixtures/` — one deliberately vulnerable file per watchlist item in `SKILL.md`.
  These are **not** examples to copy. Every file here is insecure on purpose.
- `expectations.json` — what a correct finding for each fixture looks like:
  the watchlist item it maps to, a severity floor, and terms the finding is
  expected to contain.

## Structural gate (runs in CI, no model needed)

```bash
python3 scripts/eval_skill.py --check
```

Fails if a watchlist item has no fixture, a fixture is undeclared or missing, a
fixture no longer parses, or expectations reference a watchlist item that has
been removed. This is what keeps the corpus honest as `SKILL.md` evolves: add a
watchlist item without a fixture and the build goes red.

## Behavioral eval (run by hand, or in a job with an agent available)

```bash
python3 scripts/eval_skill.py --prompt        # prints the audit prompt
# ...hand that to the agent under test, save its JSON as findings.json...
python3 scripts/eval_skill.py --grade findings.json
```

Grading reports per-fixture `PASS` / `UNDER` (found, but under-severity) /
`MISS`, plus overall recall. Anything short of full recall exits non-zero — an
advertised watchlist item that goes undetected is a regression.

Run it after editing `references/`, `SKILL.md`, or the checklists, so guidance
changes are measured rather than assumed.

The corpus is excluded from the shipped `.skill` archive.
