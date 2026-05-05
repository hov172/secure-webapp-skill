# Authorization

Covers OWASP ASVS chapter V8. This is the most commonly broken thing in AI-assisted code, and it's usually a flat-out missing check rather than a subtle bug.

> **2025 Top 10 framing:** OWASP Top 10 2025 keeps Broken Access Control at A01 (the #1 most serious application security risk) and consolidates SSRF (formerly A10:2021) into this category — recognizing that SSRF is access control failing in the *server-to-server* direction. The detailed SSRF defenses live in `secure-coding.md`; this reference covers user-to-resource access control. Both are forms of the same underlying failure: insufficient enforcement of who/what is allowed to access what.

## OWASP source sync

Deterministic notes regenerated from the refreshed OWASP source cache.

- Object-level checks: scope queries by owner or org; do not rely on authentication alone.
- Mass assignment: allowlist writable fields and block role, tenant, and owner changes.
- Multi-tenant apps: enforce membership and role checks per tenant boundary.
- Use 404 for hidden resources and 403 for visible actions the user may not take.
## The shape of the problem

Authorization answers: **given that we know who the user is, are they allowed to do this specific operation on this specific resource?**

Authentication is "who are you?". Authorization is everything else. A flaw here means a logged-in user can read or modify data that doesn't belong to them — almost always the most damaging vulnerability in a typical SaaS app, because it's silent (no failed login alerts), targeted (attackers know what they're after), and undetectable from the outside if the API responds normally.

The OWASP shorthand is **IDOR — Insecure Direct Object Reference** — but the broader concept is "broken access control", which has been #1 on the OWASP Top 10 for several cycles running.

## The three checks every protected operation needs

For any handler that touches a resource (read, write, delete), three questions:

1. **Is the user authenticated?** (Auth check — usually middleware.)
2. **Does the user have the right role/permission for this *type* of operation?** (Function-level check — "can this user invite team members at all?")
3. **Does this specific resource belong to the user, or is it shared with them?** (Object-level check — "is *this specific* invoice their invoice?")

**Step 3 is the one that gets skipped.** AI-generated CRUD handlers tend to look like:

```javascript
// BROKEN
app.get('/api/orders/:id', requireAuth, async (req, res) => {
  const order = await db.orders.findById(req.params.id);
  res.json(order);
});
```

This authenticates the user but never checks ownership. Any logged-in user can request `/api/orders/12345` and get someone else's order.

The fix patterns:

```javascript
// FIX 1: Filter at the query level (preferred — don't fetch what they can't access)
app.get('/api/orders/:id', requireAuth, async (req, res) => {
  const order = await db.orders.findOne({
    where: { id: req.params.id, userId: req.user.id }
  });
  if (!order) return res.status(404).end();
  res.json(order);
});

// FIX 2: Check after fetch (less ideal — still works)
app.get('/api/orders/:id', requireAuth, async (req, res) => {
  const order = await db.orders.findById(req.params.id);
  if (!order || order.userId !== req.user.id) return res.status(404).end();
  res.json(order);
});
```

Note the response is `404`, not `403`. Returning `403` confirms the resource exists, leaking information.

## Where to enforce: deny by default

Authorization should be enforced **server-side, at the data-access layer or in the route handler — not just in middleware that decides whether to render a UI element**. The client may not even render the "delete" button, but if a curl request to `DELETE /api/items/123` works without an ownership check, the protection is fictional.

**Default deny.** Routes should be locked by default and explicitly opened up:

```javascript
// Good: every route requires auth unless explicitly public
app.use(requireAuth);
app.get('/api/public/health', skipAuth, (req, res) => res.json({ok: true}));

// Bad: routes are open by default and you have to remember to lock them
app.get('/api/orders/:id', (req, res) => { /* no auth! */ });
```

For role checks, prefer policy/permission helpers over inline conditions:

```python
# Cluttered, easy to miss a check
@app.route('/api/teams/<team_id>/invite')
def invite(team_id):
    if current_user.role != 'admin' or current_user.team_id != team_id:
        abort(403)
    ...

# Cleaner, more reviewable
@app.route('/api/teams/<team_id>/invite')
@require_permission('team:invite', team_id_param='team_id')
def invite(team_id):
    ...
```

## Common authorization patterns

### Single-tenant per-user resources

Every record has an `owner_id` (or `user_id`) column. Every query filters by it. This is the simplest model and the right starting point for personal apps.

### Multi-tenant SaaS (organizations / workspaces)

Resources belong to an *organization*, not directly to a user. Users are members of orgs, possibly with different roles per org. Two filters now apply:

1. The resource's `org_id` matches one of the user's org memberships.
2. The user's role in that org permits the action.

This is where row-level security in the database (Postgres RLS, Supabase) genuinely earns its keep — you set the current org/user as session variables and let the DB enforce isolation, so a missed check in application code can't leak data.

### Role-based access control (RBAC)

Users have roles (admin, editor, viewer). Roles map to a set of permissions (`team:invite`, `billing:view`, `project:delete`). Permissions are checked at the operation level. Roles are scoped to a context (an org, a team, a project) — not global.

### Attribute-based / relationship-based (ReBAC)

For more complex relationships (Google Docs-style sharing, GitHub-style repo permissions), tools like OPA, Cedar, OpenFGA, or Permify model arbitrary relationships. Worth reaching for when ad-hoc role checks become unmaintainable.

### "I'm an admin" override

Admin users typically need to access any tenant's data. The risk: confusing per-user data access with admin support access. Two patterns to follow:

- **Audit every admin override.** When an admin views a user's data, log it with the admin's ID, the target user, and the reason. The audit trail is the deterrent.
- **Make it visually distinct.** Admin-as-user views should be clearly labeled in the UI, ideally in a different color, with a banner. Prevents the admin from confusing whose data they're looking at.
- **Don't log admins in as the user.** Use an "act as" mechanism that preserves their identity.

## Operations that need extra care

### Bulk operations

`PATCH /api/items` with a list of IDs. Each ID must be ownership-checked individually — not just the first one, not just N=1 sample.

```python
# BROKEN — fetches all items, applies update to all, ownership only checked for first
def bulk_update(ids, data):
    items = Item.objects.filter(id__in=ids)
    if items[0].owner_id != current_user.id:  # NO
        abort(403)
    items.update(**data)

# FIXED — filter scope by ownership in the query itself
def bulk_update(ids, data):
    Item.objects.filter(id__in=ids, owner_id=current_user.id).update(**data)
    # Anything not owned by current_user is silently excluded
```

### Mass assignment

When an update accepts a JSON body and applies fields to a model, an attacker may include fields they shouldn't be able to set:

```javascript
// User sends: { name: "new", role: "admin", isVerified: true }
await User.update({ ...req.body }, { where: { id: req.user.id }});
// Now they're an admin
```

Always allowlist updatable fields:

```javascript
const { name, bio, avatarUrl } = req.body;
await User.update({ name, bio, avatarUrl }, { where: { id: req.user.id }});
```

In Rails: use `params.require(:user).permit(:name, :bio)`. In Django REST Framework: explicit `Meta.fields` on serializers, never `__all__` for user-facing serializers. In NestJS: DTOs with `@Expose`/`whitelist: true`. Check that the framework is configured to drop unknown fields, not silently include them.

### Role/permission changes

A user editing their own profile must not be able to change their role, tenant, or owner_id. This is a special case of mass assignment but worth calling out.

### Resource creation with parent reference

When creating a child resource (`POST /api/projects/:projectId/issues`), check that the user can write to the parent (`projectId`). Don't trust the `projectId` in the URL just because the route matches.

### State machine transitions

Some operations are only valid in specific states (a draft order can be canceled; a shipped order can't). Check the current state server-side, atomically with the update. Don't trust the client's view of the state.

## What "404 vs 403" actually means

Both are valid responses to "you can't access this", but they leak different information:

- **404 Not Found** — "as far as you're concerned, this resource doesn't exist". Use this when the resource itself shouldn't be discoverable. Default for unowned resources.
- **403 Forbidden** — "the resource exists, you're authenticated, but you can't do this". Use when the user knows the resource exists (e.g., they own a parent resource) but can't perform a specific action.

Use 404 for object-level access denial, 403 for function-level. When in doubt, 404.

For unauthenticated requests: 401 Unauthorized.

## Authorization checklist

When reviewing or building any authenticated endpoint:

- [ ] Authentication is required by default; public routes are explicit exceptions
- [ ] Function-level check: does this user's role permit this operation?
- [ ] Object-level check: filter the query by ownership/membership, or assert it after fetch
- [ ] Bulk operations filter by ownership in the query, not just the first item
- [ ] Update payloads use an explicit allowlist of fields (no mass assignment)
- [ ] Role/tenant/owner fields cannot be self-modified except through dedicated admin paths
- [ ] State transitions are validated against current server state, atomically
- [ ] 404 for unowned resources (don't confirm existence); 403 for forbidden actions on visible resources
- [ ] Admin overrides are logged with admin ID, target user, and timestamp
- [ ] (For SaaS) row-level security or equivalent is considered for cross-tenant leak prevention

## Quick test for any handler

Before considering a handler done, ask: *"If I copy this URL/request from user A's session, paste it into user B's browser, and remove or alter the auth, what happens?"* If the answer involves data leaking or state changing, the check is missing or wrong.
