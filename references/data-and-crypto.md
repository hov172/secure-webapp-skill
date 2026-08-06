# Data Protection and Cryptography

Covers OWASP ASVS V11 (Cryptography) and V14 (Data Protection). For password hashing specifically, see `auth-and-sessions.md`.

## The cardinal rule

**Use vetted libraries; do not implement cryptographic primitives yourself.** Even people who do this for a living make subtle mistakes. The right level of "doing crypto" for application developers is choosing the right algorithm and parameters, and using a high-level library that exposes a hard-to-misuse API.

The libraries to reach for:

- **Python:** `cryptography` (`Fernet` for symmetric, high-level recipes). Avoid `pycrypto` (unmaintained) and `pycryptodome` for new code unless you have a specific reason.
- **Node:** the built-in `crypto` module is fine for most things; `tweetnacl` or `libsodium-wrappers` (sodium) for high-level primitives.
- **Go:** `crypto/...` from stdlib; `golang.org/x/crypto/nacl/...` for higher-level.
- **Rust:** `ring`, `rustcrypto`, or `sodiumoxide`.
- **Java:** JCA / JCE; Tink (Google's high-level library, recommended).
- **General:** Tink and libsodium are designed to be hard to misuse — strongly preferred when available.

## Algorithm choices in 2025+

### Symmetric encryption (encrypting data at rest, in transit between services)

- **AES-256-GCM** — the standard. Authenticated encryption (encrypts + authenticates). Require unique nonces per message.
- **ChaCha20-Poly1305** — equally good, often faster on platforms without AES hardware acceleration. Especially good for mobile.
- **AES-128-GCM** — fine. 128-bit security is still acceptable.

What NOT to use:

- AES-CBC without HMAC (no authentication → padding oracle, modification attacks).
- AES-ECB (deterministic; same plaintext → same ciphertext, leaks structure).
- DES, 3DES, RC4, Blowfish — all broken or deprecated.

For "I just want to encrypt this blob," use Fernet (Python) / libsodium's secretbox / Tink's `Aead` primitive. They make the right choices automatically.

### Hash functions

- **SHA-256, SHA-384, SHA-512, SHA-3, BLAKE2** — fine for general use (file integrity, content hashing).
- **MD5, SHA-1** — broken (collisions). Don't use for anything security-relevant.

These are NOT for password hashing — see `auth-and-sessions.md`. They are also NOT for HMAC keys directly — use HMAC primitives.

### Message authentication

- **HMAC-SHA-256** — for authenticating data with a shared secret.
- **AEAD modes (GCM, ChaCha20-Poly1305)** — handle authentication as part of encryption.

Don't roll your own MAC by appending a hash of (key + message); that's not secure (length-extension attacks).

### Asymmetric

- **Ed25519** — preferred for signatures. Fast, hard to misuse.
- **RSA-2048 or RSA-3072** — acceptable. Use OAEP for encryption padding (not PKCS#1 v1.5), PSS for signatures.
- **ECDSA P-256, P-384** — acceptable for signatures.
- **X25519** — preferred for key agreement.

What NOT to use:

- RSA < 2048 bits.
- DSA.
- Curves below P-256.

### Random number generation

- **Always** use a cryptographically secure RNG for security-relevant values.
- Python: `secrets` module (`secrets.token_bytes(32)`, `secrets.token_urlsafe(32)`).
- Node: `crypto.randomBytes(32)`, `crypto.randomUUID()` (v15+).
- Go: `crypto/rand`.
- Java: `SecureRandom`.

What NOT to use: `Math.random()` (JS), `random` (Python), `rand()` (C), `java.util.Random`. They're for simulations, not security.

### Key sizes for tokens

- **Session IDs, password reset tokens, API keys, CSRF tokens, anti-forgery values:** ≥128 bits, easier to ≥256 bits. `crypto.randomBytes(32)` (32 bytes = 256 bits) is a good default.

## Encrypting data at rest

The threat: someone gets a copy of your database backup, your S3 bucket, or your laptop. Plaintext sensitive data → game over.

### Encryption at the storage layer

- **Cloud-managed databases** (RDS, Cloud SQL, Azure SQL): enable storage-level encryption. It's free and handles the case of someone walking off with a disk. It does NOT protect against application bugs that read the data, or against credentials being stolen.
- **Object storage** (S3, GCS): SSE on by default in most clouds now. Verify.
- **Backups:** encrypted at rest, with keys separate from the production keys.

### Application-layer encryption (envelope encryption)

For data you want to protect even if the database is dumped (PII, secrets stored on behalf of users, payment card data, health records):

1. Generate a random data encryption key (DEK) for each record (or each tenant, or each batch — depends on access pattern).
2. Encrypt the data with the DEK using AES-256-GCM.
3. Encrypt the DEK with a key encryption key (KEK) held in your KMS (AWS KMS, GCP KMS, HashiCorp Vault, etc.).
4. Store the encrypted data + encrypted DEK; the KEK never leaves the KMS.

To read: ask KMS to decrypt the DEK, decrypt the data with the DEK in memory, never store the DEK plaintext.

This means the database alone doesn't yield plaintext — KMS access is also required.

### Tokenization for high-value data

For payment cards (PCI scope), social security numbers, government IDs: don't store them at all if you can avoid it. Use a tokenization service (Stripe, Spreedly, Skyflow, Basis Theory) that returns a token your app stores instead. Out of your scope, off your liability.

## PII handling

Personally Identifiable Information needs different handling depending on jurisdiction (GDPR in EU, CCPA in California, HIPAA for US health, etc.). Practical principles common to all:

### Minimize collection

Collect only what's needed for the user's stated purpose. Each unnecessary field is a future liability.

### Document what you collect

A simple data inventory — even a markdown file in the repo — listing each PII field, its purpose, where it's stored, who has access, and retention. Required by most privacy laws; useful regardless.

### Retention limits

PII shouldn't live forever. Define retention windows (e.g., "delete inactive accounts after 3 years"; "anonymize order data after 7 years per tax law"). Implement, schedule, verify.

### User rights

- **Access:** the user can request a copy of their data.
- **Correction:** the user can fix errors.
- **Deletion:** the user can request deletion (some exceptions for legal retention).

Build these as proper features, not as ad-hoc DB queries that get re-discovered every time. They'll be needed.

### Pseudonymization vs anonymization

- **Pseudonymized:** the data is stripped of direct identifiers but could be re-identified with additional info. Still subject to most privacy regulations.
- **Anonymized:** truly cannot be re-identified. Often harder than it looks (combinations of "non-identifying" fields can re-identify).

Don't claim "anonymous" lightly.

## Client-side data

Data on the client is at risk from XSS, malicious browser extensions, shared computers, and sync mechanisms (cloud-synced clipboard, browser sync).

- **Don't store more than necessary** in localStorage / sessionStorage / IndexedDB.
- **Don't store secrets, tokens with broad scope, or sensitive personal data** on the client.
- **Mark sensitive form fields** with `autocomplete="off"` (login, MFA codes, payment fields handled by your tokenizer).
- **Clear sensitive data on logout** — don't leave caches around.
- **Set `Cache-Control: no-store`** on pages/responses with sensitive content to prevent browser cache disclosure on shared devices.

## Encryption in transit

Always TLS for anything carrying user data. The non-obvious places people forget:

- **Service-to-service in a private network.** Don't assume the network is private; many incidents start as cloud lateral movement. Mutual TLS or mTLS-equivalent (service mesh, cloud IAM-authenticated API endpoints).
- **Database connections.** Configure clients to require TLS and verify the server certificate.
- **Webhooks.** Always HTTPS. Verify the receiver actually validated the cert.
- **Logging/monitoring outbound.** Some logging libraries default to plaintext.

Configure TLS:

- **TLS 1.2 minimum**, TLS 1.3 preferred.
- **Disable old protocols** (SSL 3.0, TLS 1.0, TLS 1.1) at the edge.
- **Strong cipher suites** — most modern frameworks/load balancers/WAFs have a "modern" preset that does the right thing.
- **HSTS** at the application layer (see `frontend-and-headers.md`).
- **Don't disable cert verification** in clients. `verify=False` (Python requests), `rejectUnauthorized: false` (Node), `--insecure` (curl) — common in dev, dangerous in prod.

## Common cryptographic mistakes

- **Reusing nonces in GCM.** GCM with a repeated nonce + same key catastrophically breaks confidentiality and authenticity. Use a counter or a random 96-bit nonce per message; keep the operation count below 2^32 for a given key with random nonces.
- **Hardcoding IVs/keys.** Never. Generate, store properly.
- **Encrypt-then-MAC vs. MAC-then-encrypt vs. Encrypt-and-MAC** — use AEAD instead and never have to think about it again.
- **"I'll just XOR with a key"** — for "just hiding things in transit"-type quick fixes. Doesn't work, even slightly. Use AEAD.
- **Storing encryption keys next to the data they encrypt** — defeats the point.
- **Not rotating keys** — eventually a key leaks; without rotation tooling, you can't respond.
- **Custom protocol design** — extremely hard to do right. Use TLS, JOSE (JWT/JWS/JWE), libsodium primitives, or Tink. Don't invent.

## Quick checklist

- [ ] Symmetric encryption uses AES-GCM or ChaCha20-Poly1305 (AEAD)
- [ ] Asymmetric uses Ed25519 / X25519 / RSA-2048+
- [ ] Random values from CSPRNG (`secrets`, `crypto.randomBytes`, etc.) — never `Math.random`
- [ ] No MD5/SHA-1 for security-relevant hashing
- [ ] Sensitive data encrypted at rest (storage-layer + envelope encryption for high-value)
- [ ] Encryption keys in KMS or secrets manager, not in code or DB
- [ ] Card / SSN / etc. data tokenized via a third party where possible
- [ ] PII inventory documented; retention windows defined; user-rights flows built
- [ ] TLS 1.2+ enforced on all external endpoints; cert verification not disabled
- [ ] Service-to-service traffic encrypted (mTLS or equivalent)
- [ ] No client-side storage of secrets or broad-scope tokens
- [ ] Logout clears sensitive client-side caches
