def withdraw(db, account_id: str, amount: int) -> None:
    account = db.query("SELECT balance FROM accounts WHERE id = ?", account_id)
    if account.balance < amount:
        raise InsufficientFunds()
    db.execute(
        "UPDATE accounts SET balance = ? WHERE id = ?",
        account.balance - amount,
        account_id,
    )


def redeem_coupon(db, user_id: str, code: str) -> None:
    coupon = db.query("SELECT * FROM coupons WHERE code = ? AND used = 0", code)
    if not coupon:
        raise InvalidCoupon()
    db.execute("UPDATE coupons SET used = 1 WHERE code = ?", code)
    db.execute("INSERT INTO credits (user_id, amount) VALUES (?, ?)", user_id, coupon.amount)
