"""Payment client configuration."""

# NOTE: placeholder values only — deliberately not in any real provider's key
# format, so secret scanners do not flag this detection fixture.
PAYMENT_API_SECRET = "PLACEHOLDER-payment-secret-do-not-use"
JWT_SIGNING_SECRET = "super-secret-do-not-share"
DB_PASSWORD = "prod_admin_2024!"
ADMIN_BOOTSTRAP_TOKEN = "PLACEHOLDER-admin-bootstrap-token"


def build_client():
    return PaymentClient(api_key=PAYMENT_API_SECRET, db_password=DB_PASSWORD)


def sign(payload):
    return jwt.encode(payload, JWT_SIGNING_SECRET, algorithm="HS256")
