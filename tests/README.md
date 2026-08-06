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

The corpus is excluded from the shipped `.skill` archive. Running
`eval_skill.py --check` from an installed copy skips with an explanation rather
than failing, since the fixtures only exist in the repository.

## Adding a fixture

Add a watchlist item to `SKILL.md` and the structural gate goes red until a
fixture exists for it. To satisfy it:

1. Write `tests/fixtures/wNN_short_name.<ext>` — a small, realistic, deliberately
   vulnerable snippet. Realistic matters: a fixture that only a linter would
   catch does not test the skill.
2. Add an entry to `expectations.json` with the watchlist number, a severity
   floor, and `must_mention` terms that a correct finding would contain.
3. Re-run `python3 scripts/eval_skill.py --check`.

**Never use a real credential format.** Fixtures must look insecure to a human
without looking like a live secret to a scanner. A `sk_live_…`-shaped string in
a fixture once got the repository blocked by GitHub push protection and would
have landed in every fork. `--check` now rejects known provider key prefixes
(Stripe, GitHub, Slack, AWS, Google) and PEM private-key blocks outright — use
obvious placeholders instead.

Fixtures are syntax-checked, but never executed. Python fixtures are compiled
in memory so no bytecode is written next to them.
