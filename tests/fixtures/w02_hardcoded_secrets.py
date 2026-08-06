"""Payment client configuration."""

# Every value below is an obvious placeholder, chosen so secret scanners do not
# flag this detection fixture. The vulnerability under test is that credentials
# are hardcoded at all — not the strings themselves.
PAYMENT_API_SECRET = "PLACEHOLDER-payment-api-secret"
JWT_SIGNING_SECRET = "PLACEHOLDER-jwt-signing-secret"
DB_PASSWORD = "PLACEHOLDER-database-password"
ADMIN_BOOTSTRAP_TOKEN = "PLACEHOLDER-admin-bootstrap-token"


def build_client():
    return PaymentClient(api_key=PAYMENT_API_SECRET, db_password=DB_PASSWORD)


def sign(payload):
    return jwt.encode(payload, JWT_SIGNING_SECRET, algorithm="HS256")
