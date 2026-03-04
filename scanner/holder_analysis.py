"""
Holder concentration analysis — works purely on audit_contract() output.
No extra API calls needed; GoPlus already includes holder data.
"""


def analyze_holders(audit: dict) -> dict:
    """
    Analyze holder concentration from GoPlus audit data.

    Args:
        audit: Output of scanner.contract_audit.audit_contract()

    Returns:
        Concentration summary dict. Contains "error" key if data unavailable.
    """
    if "error" in audit:
        return {"error": audit["error"]}

    holders = audit.get("holders", [])
    lp_holders = audit.get("lp_holders", [])

    if not holders:
        return {"error": "No holder data returned by GoPlus for this contract"}

    # Top 10 concentration
    top10_pct = sum(float(h.get("percent", 0)) for h in holders[:10]) * 100

    # Insider addresses (owners + creators)
    insider_addresses = {
        addr.lower()
        for group in (audit.get("owners", []), audit.get("creators", []))
        for item in group
        if (addr := item.get("address", ""))
    }

    insider_pct = sum(
        float(h.get("percent", 0))
        for h in holders
        if h.get("address", "").lower() in insider_addresses
    ) * 100

    # LP analysis
    top_lp_pct = float(lp_holders[0].get("percent", 0)) * 100 if lp_holders else 0.0
    lp_locked = any(h.get("is_locked") == 1 for h in lp_holders)

    return {
        "holder_count": audit.get("holder_count", 0),
        "top10_concentration_pct": round(top10_pct, 2),
        "insider_holdings_pct": round(insider_pct, 2),
        "top_lp_holder_pct": round(top_lp_pct, 2),
        "lp_locked": lp_locked,
        "top_holders": holders[:10],
    }
