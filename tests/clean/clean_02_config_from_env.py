"""Payment client configuration.

Credentials come from the environment and are never written to the repository.
Missing configuration fails loudly at startup rather than defaulting.
"""

import os


def _required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"missing required configuration: {name}")
    return value


def build_client() -> "PaymentClient":
    return PaymentClient(
        api_key=_required("PAYMENT_API_KEY"),
        db_password=_required("DATABASE_PASSWORD"),
    )
