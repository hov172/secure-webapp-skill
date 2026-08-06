def can_access(user, document) -> bool:
    try:
        return authz_service.check(user.id, document.id)
    except Exception:
        # Don't block the user if the authz service is having a bad day.
        return True


def rate_limited(key: str) -> bool:
    try:
        return redis.incr(key) > 100
    except Exception:
        return False
