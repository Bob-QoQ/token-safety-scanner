"""
Risk scorer — pure calculation, no API calls.
Score: 0-100, higher = safer.
"""


def score(audit: dict, holders: dict, whale: dict) -> dict:
    """
    Calculate a risk score from audit + holder + whale data.

    Returns:
        Dict with "score" (int), "rating" (str), "flags" (list of str).
    """
    points = 100
    flags = []

    # ── Contract risks ────────────────────────────────────────────────
    if audit.get("is_honeypot"):
        points -= 50
        flags.append("HONEYPOT DETECTED")

    if not audit.get("is_open_source"):
        points -= 15
        flags.append("Contract source not verified")

    if audit.get("is_mintable"):
        points -= 15
        flags.append("Owner can mint unlimited tokens")

    if audit.get("hidden_owner"):
        points -= 15
        flags.append("Hidden owner detected")

    if audit.get("can_take_back_ownership"):
        points -= 10
        flags.append("Owner can reclaim contract ownership")

    if audit.get("selfdestruct"):
        points -= 10
        flags.append("Contract has selfdestruct function")

    if audit.get("transfer_pausable"):
        points -= 8
        flags.append("Transfers can be paused by owner")

    if audit.get("is_blacklisted"):
        points -= 8
        flags.append("Blacklist function exists")

    if audit.get("cannot_sell_all"):
        points -= 8
        flags.append("Cannot sell all tokens (potential honeypot)")

    if audit.get("slippage_modifiable"):
        points -= 5
        flags.append("Slippage can be modified by owner")

    if audit.get("owner_change_balance"):
        points -= 10
        flags.append("Owner can change token balances")

    # ── Tax ───────────────────────────────────────────────────────────
    buy_tax = audit.get("buy_tax", 0)
    sell_tax = audit.get("sell_tax", 0)
    if buy_tax > 10 or sell_tax > 10:
        points -= 10
        flags.append(f"High tax: buy {buy_tax:.1f}% / sell {sell_tax:.1f}%")
    elif buy_tax > 5 or sell_tax > 5:
        points -= 5
        flags.append(f"Elevated tax: buy {buy_tax:.1f}% / sell {sell_tax:.1f}%")

    # ── Holder concentration ──────────────────────────────────────────
    if "error" not in holders:
        top10 = holders.get("top10_concentration_pct", 0)
        insider = holders.get("insider_holdings_pct", 0)
        holder_count = holders.get("holder_count", 0)

        if top10 > 80:
            points -= 15
            flags.append(f"Extreme concentration: top 10 hold {top10:.1f}%")
        elif top10 > 50:
            points -= 8
            flags.append(f"High concentration: top 10 hold {top10:.1f}%")

        if insider > 20:
            points -= 15
            flags.append(f"Insider holdings very high: {insider:.1f}%")
        elif insider > 10:
            points -= 8
            flags.append(f"Insider holdings elevated: {insider:.1f}%")

        if holder_count < 100:
            points -= 5
            flags.append(f"Very few holders: {holder_count}")

        if not holders.get("lp_locked"):
            points -= 5
            flags.append("LP not locked - rug pull risk")

    points = max(0, min(100, points))

    if points >= 80:
        rating = "SAFE"
    elif points >= 60:
        rating = "CAUTION"
    elif points >= 40:
        rating = "RISKY"
    else:
        rating = "DANGER"

    return {
        "score": points,
        "rating": rating,
        "flags": flags,
    }
