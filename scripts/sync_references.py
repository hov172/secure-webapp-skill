#!/usr/bin/env python3
"""Deterministically sync curated references from refreshed OWASP source cache.

This is a no-API-key path: it reads _sources/ and updates the curated
references with a small generated section derived from fixed rules.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES = ROOT / "_sources"
REFERENCES = ROOT / "references"


def fail(message: str) -> None:
    raise SystemExit(message)


def read_source(source_name: str, filename: str) -> str:
    path = SOURCES / source_name / filename
    if not path.exists():
        fail(f"missing source cache file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def has_all(texts: list[str], *needles: str) -> bool:
    haystack = "\n".join(texts).lower()
    return all(needle.lower() in haystack for needle in needles)


def add_bullet(bullets: list[str], text: str) -> None:
    if text not in bullets:
        bullets.append(text)


def sync_auth() -> list[str]:
    texts = [
        read_source("cheatsheets", "Authentication_Cheat_Sheet.md"),
        read_source("cheatsheets", "Password_Storage_Cheat_Sheet.md"),
        read_source("cheatsheets", "Session_Management_Cheat_Sheet.md"),
        read_source("cheatsheets", "Forgot_Password_Cheat_Sheet.md"),
        read_source("cheatsheets", "Multifactor_Authentication_Cheat_Sheet.md"),
        read_source("cheatsheets", "Credential_Stuffing_Prevention_Cheat_Sheet.md"),
    ]
    bullets: list[str] = []
    if has_all(texts, "Argon2id") or has_all(texts, "bcrypt") or has_all(texts, "PBKDF2"):
        add_bullet(bullets, "Password storage: Argon2id first; bcrypt is legacy; PBKDF2 is the FIPS fallback.")
    if has_all(texts, "reset", "token") and has_all(texts, "single", "use"):
        add_bullet(bullets, "Password reset: use hashed, single-use, expiring tokens and invalidate other sessions after use.")
    if has_all(texts, "Secure", "HttpOnly", "SameSite") or has_all(texts, "session", "cookie"):
        add_bullet(bullets, "Sessions: Secure, HttpOnly, SameSite cookies plus session rotation on login and privilege change.")
    if has_all(texts, "WebAuthn") or has_all(texts, "passkey") or has_all(texts, "TOTP"):
        add_bullet(bullets, "MFA: prefer passkeys/WebAuthn, then TOTP; keep SMS/email as fallback only.")
    if has_all(texts, "rate", "limit") or has_all(texts, "credential", "stuff"):
        add_bullet(bullets, "Auth flows: rate-limit login, reset, and MFA paths to slow credential stuffing.")
    return bullets


def sync_authorization() -> list[str]:
    texts = [
        read_source("cheatsheets", "Authorization_Cheat_Sheet.md"),
        read_source("cheatsheets", "Access_Control_Cheat_Sheet.md"),
        read_source("cheatsheets", "Insecure_Direct_Object_Reference_Prevention_Cheat_Sheet.md"),
        read_source("cheatsheets", "Mass_Assignment_Cheat_Sheet.md"),
        read_source("cheatsheets", "Multi_Tenant_Security_Cheat_Sheet.md"),
    ]
    bullets: list[str] = []
    if has_all(texts, "owner", "id") or has_all(texts, "query", "scope"):
        add_bullet(bullets, "Object-level checks: scope queries by owner or org; do not rely on authentication alone.")
    if has_all(texts, "bulk") or has_all(texts, "parent"):
        add_bullet(bullets, "Bulk and parent-child routes: verify ownership for every ID and parent resource.")
    if has_all(texts, "mass", "assignment") or has_all(texts, "allowlist"):
        add_bullet(bullets, "Mass assignment: allowlist writable fields and block role, tenant, and owner changes.")
    if has_all(texts, "multi", "tenant") or has_all(texts, "org"):
        add_bullet(bullets, "Multi-tenant apps: enforce membership and role checks per tenant boundary.")
    if has_all(texts, "404") or has_all(texts, "403"):
        add_bullet(bullets, "Use 404 for hidden resources and 403 for visible actions the user may not take.")
    return bullets


def sync_input() -> list[str]:
    texts = [
        read_source("cheatsheets", "Input_Validation_Cheat_Sheet.md"),
        read_source("cheatsheets", "Injection_Prevention_Cheat_Sheet.md"),
        read_source("cheatsheets", "SQL_Injection_Prevention_Cheat_Sheet.md"),
        read_source("cheatsheets", "Query_Parameterization_Cheat_Sheet.md"),
        read_source("cheatsheets", "Cross_Site_Scripting_Prevention_Cheat_Sheet.md"),
        read_source("cheatsheets", "DOM_based_XSS_Prevention_Cheat_Sheet.md"),
        read_source("cheatsheets", "OS_Command_Injection_Defense_Cheat_Sheet.md"),
        read_source("cheatsheets", "NoSQL_Security_Cheat_Sheet.md"),
        read_source("cheatsheets", "Deserialization_Cheat_Sheet.md"),
        read_source("cheatsheets", "Prototype_Pollution_Prevention_Cheat_Sheet.md"),
    ]
    bullets: list[str] = []
    if has_all(texts, "validate") or has_all(texts, "allowlist"):
        add_bullet(bullets, "Validate at the boundary; encode at the output; prefer allowlists and length caps.")
    if has_all(texts, "sql") or has_all(texts, "parameter"):
        add_bullet(bullets, "Database access: use parameterized queries or ORM query builders, never string-built SQL.")
    if has_all(texts, "innerhtml") or has_all(texts, "escape") or has_all(texts, "sanit"):
        add_bullet(bullets, "XSS defense: auto-escape by default; sanitize only when rich HTML is truly required.")
    if has_all(texts, "shell") or has_all(texts, "exec") or has_all(texts, "subprocess"):
        add_bullet(bullets, "Shell calls: use argv-form process APIs, not shell strings.")
    if has_all(texts, "csv") or has_all(texts, "formula"):
        add_bullet(bullets, "CSV exports: neutralize spreadsheet formulas and other interpreter-specific payloads.")
    return bullets


def sync_files_and_apis() -> list[str]:
    texts = [
        read_source("cheatsheets", "REST_Security_Cheat_Sheet.md"),
        read_source("cheatsheets", "GraphQL_Cheat_Sheet.md"),
        read_source("cheatsheets", "WebSocket_Security_Cheat_Sheet.md"),
        read_source("cheatsheets", "File_Upload_Cheat_Sheet.md"),
    ]
    bullets: list[str] = []
    if has_all(texts, "rate", "limit"):
        add_bullet(bullets, "API endpoints: rate-limit auth and expensive operations.")
    if has_all(texts, "pagination") or has_all(texts, "page size"):
        add_bullet(bullets, "List endpoints: require pagination and cap maximum page size.")
    if has_all(texts, "upload") or has_all(texts, "magic"):
        add_bullet(bullets, "Uploads: cap size, validate type and magic bytes, and store outside the web root.")
    if has_all(texts, "csrf") or has_all(texts, "cookie"):
        add_bullet(bullets, "Cookie-auth APIs: keep CSRF protection on all state-changing routes.")
    if has_all(texts, "graphql") or has_all(texts, "websocket"):
        add_bullet(bullets, "Programmatic APIs: default deny, per-resource auth, and schema discipline.")
    return bullets


def sync_frontend() -> list[str]:
    texts = [
        read_source("cheatsheets", "Content_Security_Policy_Cheat_Sheet.md"),
        read_source("cheatsheets", "HTTP_Headers_Cheat_Sheet.md"),
        read_source("cheatsheets", "HTTP_Strict_Transport_Security_Cheat_Sheet.md"),
        read_source("cheatsheets", "Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.md"),
        read_source("cheatsheets", "Clickjacking_Defense_Cheat_Sheet.md"),
        read_source("cheatsheets", "Cookie_Theft_Mitigation_Cheat_Sheet.md"),
    ]
    bullets: list[str] = []
    if has_all(texts, "content-security-policy") or has_all(texts, "csp"):
        add_bullet(bullets, "Browser controls: CSP plus HSTS and defensive headers on HTML responses.")
    if has_all(texts, "httponly") or has_all(texts, "samesite") or has_all(texts, "secure"):
        add_bullet(bullets, "Cookies: Secure, HttpOnly, SameSite; do not rely on credentialed wildcard CORS.")
    if has_all(texts, "frame", "ancestors") or has_all(texts, "clickjacking"):
        add_bullet(bullets, "Clickjacking: prefer CSP frame-ancestors and deny framing by default.")
    if has_all(texts, "csrf"):
        add_bullet(bullets, "CSRF: keep anti-forgery tokens or equivalent defenses for cookie-auth state changes.")
    if has_all(texts, "redirect"):
        add_bullet(bullets, "Redirects: keep destinations relative or allowlisted; reject protocol-relative URLs.")
    return bullets


def sync_crypto() -> list[str]:
    texts = [
        read_source("cheatsheets", "Cryptographic_Storage_Cheat_Sheet.md"),
        read_source("cheatsheets", "Password_Storage_Cheat_Sheet.md"),
        read_source("cheatsheets", "Key_Management_Cheat_Sheet.md"),
        read_source("cheatsheets", "Transport_Layer_Security_Cheat_Sheet.md"),
    ]
    bullets: list[str] = []
    if has_all(texts, "argon2id") or has_all(texts, "bcrypt") or has_all(texts, "pbkdf2"):
        add_bullet(bullets, "Password storage: use Argon2id, bcrypt for legacy, or PBKDF2 where FIPS is required.")
    if has_all(texts, "gcm") or has_all(texts, "chacha20"):
        add_bullet(bullets, "Encryption: prefer AEAD modes such as AES-GCM or ChaCha20-Poly1305.")
    if has_all(texts, "random") or has_all(texts, "entropy"):
        add_bullet(bullets, "Randomness: use a CSPRNG for tokens, keys, and nonces.")
    if has_all(texts, "key", "rotation"):
        add_bullet(bullets, "Keys: separate keys from data and plan for rotation.")
    if has_all(texts, "tls") or has_all(texts, "certificate"):
        add_bullet(bullets, "Transport: keep TLS verification on and avoid insecure fallback paths.")
    return bullets


def sync_supply_chain() -> list[str]:
    texts = [
        read_source("cheatsheets", "Vulnerable_Dependency_Management_Cheat_Sheet.md"),
        read_source("cheatsheets", "Software_Supply_Chain_Security_Cheat_Sheet.md"),
        read_source("cheatsheets", "Dependency_Graph_SBOM_Cheat_Sheet.md"),
        read_source("cheatsheets", "CI_CD_Security_Cheat_Sheet.md"),
        read_source("cheatsheets", "NPM_Security_Cheat_Sheet.md"),
    ]
    bullets: list[str] = []
    if has_all(texts, "lockfile") or has_all(texts, "sbom"):
        add_bullet(bullets, "Inventory: commit lockfiles and generate SBOMs for releases.")
    if has_all(texts, "floating tag") or has_all(texts, "checkout"):
        add_bullet(bullets, "CI/CD: pin GitHub Actions and other build dependencies.")
    if has_all(texts, "oidc") or has_all(texts, "long-lived"):
        add_bullet(bullets, "CI auth: prefer OIDC over long-lived cloud credentials.")
    if has_all(texts, "sign") or has_all(texts, "provenance"):
        add_bullet(bullets, "Releases: sign artifacts and keep provenance evidence.")
    if has_all(texts, "postinstall") or has_all(texts, "npm"):
        add_bullet(bullets, "Install path: limit untrusted postinstall scripts and audit dependencies.")
    return bullets


def sync_logging() -> list[str]:
    texts = [
        read_source("cheatsheets", "Logging_Cheat_Sheet.md"),
        read_source("cheatsheets", "Logging_Vocabulary_Cheat_Sheet.md"),
        read_source("cheatsheets", "Error_Handling_Cheat_Sheet.md"),
    ]
    bullets: list[str] = []
    if has_all(texts, "fail", "closed"):
        add_bullet(bullets, "Failure paths: fail closed on auth, authz, and feature-flag checks.")
    if has_all(texts, "stack") or has_all(texts, "error"):
        add_bullet(bullets, "Errors: do not leak stack traces or sensitive implementation details to clients.")
    if has_all(texts, "log") or has_all(texts, "audit"):
        add_bullet(bullets, "Logs: capture security-relevant events, but never secrets or raw auth payloads.")
    if has_all(texts, "central"):
        add_bullet(bullets, "Observability: centralize logs so incidents can be traced and alerted on.")
    return bullets


def sync_design() -> list[str]:
    texts = [
        read_source("cheatsheets", "Threat_Modeling_Cheat_Sheet.md"),
        read_source("cheatsheets", "Attack_Surface_Analysis_Cheat_Sheet.md"),
        read_source("cheatsheets", "Abuse_Case_Cheat_Sheet.md"),
        read_source("cheatsheets", "Secure_Product_Design_Cheat_Sheet.md"),
    ]
    bullets: list[str] = []
    if has_all(texts, "threat", "model"):
        add_bullet(bullets, "Design review: start with trust boundaries, abuse cases, and the failure mode.")
    if has_all(texts, "multi", "tenant"):
        add_bullet(bullets, "Multi-tenant design: make isolation explicit and review revocation paths.")
    if has_all(texts, "attack", "surface"):
        add_bullet(bullets, "Attack surface: reduce exposed features and privileged paths.")
    if has_all(texts, "secure", "by design"):
        add_bullet(bullets, "Secure-by-design: put authorization and state checks in the server, not the UI.")
    if has_all(texts, "abuse"):
        add_bullet(bullets, "Abuse thinking: ask how the feature breaks, not just how it should work.")
    return bullets


def sync_secure_coding() -> list[str]:
    texts = [
        read_source("cheatsheets", "Server_Side_Request_Forgery_Prevention_Cheat_Sheet.md"),
        read_source("cheatsheets", "Unvalidated_Redirects_and_Forwards_Cheat_Sheet.md"),
        read_source("cheatsheets", "Deserialization_Cheat_Sheet.md"),
        read_source("cheatsheets", "Prototype_Pollution_Prevention_Cheat_Sheet.md"),
    ]
    bullets: list[str] = []
    if has_all(texts, "allowlist") or has_all(texts, "private", "ip"):
        add_bullet(bullets, "SSRF: allowlist destinations and block private IPs after DNS resolution.")
    if has_all(texts, "redirect"):
        add_bullet(bullets, "Redirects: re-check every hop and reject unsafe schemes.")
    if has_all(texts, "deserialize") or has_all(texts, "pickle") or has_all(texts, "untrusted"):
        add_bullet(bullets, "Deserialization: keep untrusted data in safe formats such as JSON.")
    if has_all(texts, "prototype"):
        add_bullet(bullets, "Prototype pollution: strip dangerous keys before merging untrusted objects.")
    if has_all(texts, "timeout") or has_all(texts, "circuit"):
        add_bullet(bullets, "External calls: add timeouts and circuit breakers so failures do not cascade.")
    return bullets


SYNCERS = {
    "auth-and-sessions.md": sync_auth,
    "authorization.md": sync_authorization,
    "input-handling.md": sync_input,
    "apis-and-files.md": sync_files_and_apis,
    "frontend-and-headers.md": sync_frontend,
    "data-and-crypto.md": sync_crypto,
    "supply-chain.md": sync_supply_chain,
    "logging-and-errors.md": sync_logging,
    "insecure-design.md": sync_design,
    "secure-coding.md": sync_secure_coding,
}


def render_section(bullets: list[str]) -> str:
    lines = [
        "## OWASP source sync",
        "",
        "Deterministic notes regenerated from the refreshed OWASP source cache.",
        "",
    ]
    for bullet in bullets:
        lines.append(f"- {bullet}")
    lines.append("")
    return "\n".join(lines)


def replace_section(text: str, section: str) -> str:
    marker = "## OWASP source sync"
    if marker in text:
        before, _, tail = text.partition(marker)
        rest = tail.split("\n## ", 1)
        if len(rest) == 2:
            after = "\n## " + rest[1]
        else:
            after = ""
        return before.rstrip() + "\n\n" + section + after.lstrip()
    idx = text.find("\n## ")
    if idx == -1:
        return text.rstrip() + "\n\n" + section
    return text[:idx].rstrip() + "\n\n" + section + text[idx:]


def sync_reference(name: str, syncer) -> bool:
    path = REFERENCES / name
    original = path.read_text(encoding="utf-8")
    bullets = syncer()
    section = render_section(bullets)
    updated = replace_section(original, section)
    if updated != original:
        path.write_text(updated, encoding="utf-8")
        print(f"updated references/{name}")
        return True
    print(f"unchanged references/{name}")
    return False


def main() -> None:
    if not SOURCES.exists():
        fail("_sources not found; run scripts/refresh.py first")
    changed = False
    for name, syncer in SYNCERS.items():
        changed = sync_reference(name, syncer) or changed
    if changed:
        print("Deterministic reference sync complete")
    else:
        print("No reference updates were needed")


if __name__ == "__main__":
    main()
