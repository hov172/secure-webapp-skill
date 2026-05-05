# Insecure Design & Threat Modeling

Covers OWASP Top 10 2025 A06 (Insecure Design), which corresponds to design-level flaws — security gaps that no amount of careful implementation can fix because the right control was never specified in the first place. This is the area the original skill underweighted; vibe coders especially benefit from a few lightweight design-time habits because the iterative "build first, secure later" loop tends to bake in design flaws that are extremely expensive to remove later.

## OWASP source sync

Deterministic notes regenerated from the refreshed OWASP source cache.

- Design review: start with trust boundaries, abuse cases, and the failure mode.
- Multi-tenant design: make isolation explicit and review revocation paths.
- Attack surface: reduce exposed features and privileged paths.
- Abuse thinking: ask how the feature breaks, not just how it should work.
## The distinction that matters

- **Implementation defect** — the design said "check that the user owns this resource"; the code forgot to. Fix in the handler.
- **Design flaw** — the design never required the check, or the design assumed something that isn't true (e.g., "the client will only send valid quantities"). Fix in the design.

A perfectly implemented insecure design is still insecure. A flawed implementation of a secure design might still be exploitable but is patchable in one spot. The skill is being able to tell which kind of issue you're looking at — because the fix lives in different places.

## When design-time thinking is worth the time

For weekend prototypes: skim the **secure-design defaults** section below and stop there.

For anything that handles users' data, money, or external integrations: do a lightweight threat model when:

- Adding a new feature that crosses a trust boundary (accepts user input, integrates with a third party, exposes a new endpoint).
- Adding a new user role or permission level.
- Changing how authentication or authorization works.
- Adding multi-tenancy or sharing/collaboration features.
- Integrating with payment, healthcare, or other regulated data.
- Allowing user-supplied URLs, files, or content to be processed server-side.

The cost is 30-60 minutes; the alternative is finding the same problem after launch.

## A lightweight threat model — four questions

Adapted from the Threat Modeling Manifesto. These four questions are sufficient for most app-level features:

1. **What are we building?** Sketch the feature: where data enters, where it's stored, where it leaves, who can trigger each path. A whiteboard data-flow diagram is enough — boxes for components, arrows for data, lines for trust boundaries (where untrusted data crosses into trusted territory).

2. **What can go wrong?** Walk each component and arrow. STRIDE is a useful prompt — for each element ask whether the design is resistant to:
   - **S**poofing — can someone pretend to be someone else?
   - **T**ampering — can someone modify data they shouldn't?
   - **R**epudiation — can someone deny doing something they did?
   - **I**nformation disclosure — can someone see data they shouldn't?
   - **D**enial of service — can someone crash or overload it?
   - **E**levation of privilege — can someone gain access they shouldn't have?

3. **What are we going to do about it?** For each plausible threat: mitigate (add a control), accept (document why the risk is tolerable), transfer (insurance, third party), or avoid (change the design to remove the threat). Most decisions here are mitigations.

4. **Did we do a good enough job?** Did the controls actually land in code? Are there test cases for the abuse scenarios? Did the threat model get updated when the feature changed? This is the question most often skipped.

The output is a short doc — a paragraph or three of "here's what we considered, here's what we're doing about it, here's what we accepted." Save it next to the feature spec.

## Secure-design defaults (apply without ceremony)

These are design choices to make as a matter of course on any web app, no formal threat model required. Most have already shown up in other references; collected here as the design-time view.

**Identity & access:**
- Default deny — every protected resource requires explicit authorization. New routes are locked by default.
- Centralize authentication and session checks in middleware, not per-handler.
- Centralize authorization decisions where reasonable (a `can(user, action, resource)` function or a policy engine), so adding a new check in one place doesn't miss N other places.
- Trust boundaries are explicit. Document where untrusted data enters and assume it's hostile until validated/encoded.

**Data:**
- Minimize what you collect. Each unnecessary field is future liability.
- Sensitive data has a documented retention period. Build the deletion path early.
- PII gets logged deliberately, not accidentally.
- Customer data has a path for export and deletion (regulatory necessity for most apps).

**State changes:**
- State machines for any non-trivial workflow (orders, subscriptions, multi-step flows). Validate transitions server-side, atomically. Don't trust the client's view of "what step we're on."
- Idempotency keys for anything the client retries (payments, webhook processing, anything POST-shaped).
- Atomic operations for shared resources — a check-then-write race condition is a design issue, not a coding mistake.

**Failure modes (this connects to A10 — see `logging-and-errors.md`):**
- **Fail closed** — when something unexpected happens, deny rather than allow. An auth service that's unreachable should not result in "user authenticated."
- Roll back partial transactions completely. Halfway-completed state changes are how attackers find races.
- Document the failure mode of each external dependency (what happens when Stripe is down? When the email provider rate-limits us?).

**Boundaries between tenants/users:**
- For multi-tenant: tenant ID is in every query, ideally enforced at the data layer (row-level security, dedicated schemas, etc.) — not just in application code.
- Bulk operations can't cross tenants — operations scoped at the query level rather than filtering after fetch.
- Admin "act as user" features are visually distinct, audit-logged, and time-limited.

**Inputs and outputs:**
- All input is untrusted by default — including from authenticated users, from your own services, from your own database when the data originated as user input.
- All output is encoded for its destination context.
- Integration points (webhooks, callbacks, third-party APIs) are treated as adversary-controlled.

**Plausibility checks at each tier:**
- Frontend validates for UX. Backend validates for security. Database constraints validate for integrity. None alone is sufficient.
- Reasonable bounds on every numeric input (no `quantity: 999999999` accepted silently).
- Rate limits at the perimeter and at expensive operations.

## Common design-flaw patterns to recognize

These are recurring shapes that show up in vibe-coded apps and are usually fixable only by changing the design, not by patching the code:

**Implicit trust between client and server.** "The client only sends valid data because our UI prevents otherwise." The UI doesn't bind attackers. Design assumes the wire format is hostile.

**Authorization done in the UI.** "The 'delete' button only shows for admins, so we don't need a server-side role check." The button is a hint to the user, not a security control.

**Shared keys for unrelated purposes.** Reusing the same secret for JWT signing, cookie signing, password reset tokens, and webhook HMAC. A leak in one path compromises all four.

**Implicit ordering / state assumptions.** "Step 3 only happens after step 1 and 2 because the UI walks the user through them." Direct API calls to step 3 don't follow the UI's flow.

**No path for user data deletion.** "We'll figure it out when someone asks." GDPR, CCPA, and most modern privacy frameworks require it; retrofitting deletion is much harder than building it.

**No path for credential rotation.** Hardcoded service-account credentials, JWT signing keys, encryption keys with no key ID. When (not if) one leaks, the response is "redeploy everything."

**No multi-tenancy until later.** Building single-tenant first, intending to add tenant isolation later. The migration is brutal — every query, every index, every test, every cache key.

**Authentication ≠ authorization.** Designs that conflate "user is logged in" with "user can do X" lead to systems where any logged-in user can do anything via the API.

**Treating bots like humans.** Login forms that work fine for humans get destroyed by credential-stuffers; signup forms get spam-filled; rate-limited APIs get hammered. Anti-automation belongs in the design, not the post-launch patch.

**Race conditions in financial flows.** Balance-check-then-debit without a transaction, "first one wins" promo codes without atomic decrement, idempotency assumed but not enforced.

## Two example threat models (vibe-coder scale)

### Example 1: "Add a profile picture upload"

**What are we building?** Endpoint accepts an image upload, resizes, stores in S3, displays on profile.

**What can go wrong?**
- *Spoofing:* none new.
- *Tampering:* user uploads a file pretending to be an image but it's HTML/SVG/PHP — could become stored XSS or RCE.
- *Repudiation:* low.
- *Information disclosure:* upload path includes user-controlled filename → path traversal? EXIF reveals location?
- *DoS:* huge file uploads exhaust memory/disk; ImageMagick known for parser bugs that can hang on crafted input.
- *Elevation of privilege:* none direct, but stored-XSS via SVG could escalate.

**What are we going to do about it?**
- Cap upload size at the proxy and framework level (5MB).
- Validate magic bytes; allowlist JPEG/PNG/WebP only; explicitly reject SVG.
- Re-encode through Pillow with a known-good config — not ImageMagick.
- Strip EXIF during re-encode.
- Generate server-side filename; don't trust client name; store under user-prefixed key.
- Serve with `Content-Disposition: inline` and explicit `Content-Type: image/png`, plus `X-Content-Type-Options: nosniff`.
- Rate-limit upload endpoint per user (e.g., 10/hour).

**Did we do a good enough job?** Tests for: oversize upload, mismatched magic bytes, SVG rejection, traversal attempt in filename, re-fetched image has no EXIF.

### Example 2: "Add a 'share with email' feature"

**What are we building?** User enters a recipient email; we send a tokenized link granting view access to a document.

**What can go wrong?**
- *Tampering:* token is guessable → access to any doc.
- *Information disclosure:* recipient field accepts any email — used as spam relay? Sender's name in the email?
- *DoS:* attacker fires off thousands of share-emails to fatigue our reputation with email providers.
- *Elevation of privilege:* tokenized link bypasses our normal auth → recipient gets perpetual access.

**What are we going to do about it?**
- Tokens: 256-bit random, hashed in DB, single-use, expire in 7 days.
- Rate-limit shares per sender (e.g., 50/day) and per recipient address (10/day to same address).
- Email is from a no-reply address with the sender's name in the body, not the From header (no spoofing).
- Recipient must click and re-authenticate (or sign up) before access — token is auth-elevation, not standalone access.
- Sender can revoke shares from a "shared with" UI; system surfaces still-valid shares.
- Audit log: who shared what with whom and when.

**Did we do a good enough job?** Tests for token reuse, expired token rejection, rate-limit triggering, revoke-after-share invalidates the link.

## Quick checklist when designing a new feature

- [ ] Sketched the data flow and trust boundaries
- [ ] Considered each STRIDE category briefly (5–10 min, not a project)
- [ ] Default-deny on any new endpoint or resource
- [ ] Identified what's untrusted input and where it gets validated/encoded
- [ ] Identified failure modes and decided how the system fails (closed, hopefully)
- [ ] Identified rate limits / quotas / bounds
- [ ] Identified what gets logged, what gets audited, what's PII
- [ ] Documented enough for review (a few paragraphs is usually enough)
- [ ] Tests cover the abuse cases, not just the happy path

## When it's tempting to skip this

Three signals that it's exactly the time NOT to skip:

1. **"This is just an MVP."** The MVP becomes prod faster than anyone admits. Design flaws baked in at MVP often survive to GA.
2. **"The framework handles security."** Frameworks handle implementation hazards (CSRF tokens, parameterized queries). They don't make design decisions for you.
3. **"It's an internal tool."** Internal tools handle real data, get exposed accidentally (a misconfigured proxy, an SSO mistake), and get less security review than external products.

The 30 minutes spent on a back-of-envelope threat model is consistently the cheapest security investment in any feature.
