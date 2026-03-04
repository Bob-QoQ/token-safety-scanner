"""
Contract audit scanner — wraps GoPlus data into a clean, typed dict.
"""
from adapters.goplus import get_token_security


def audit_contract(chain_id: str, contract_address: str) -> dict:
    """
    Run a contract security audit via GoPlus.

    Returns:
        Structured audit dict. Contains "error" key if lookup failed.
    """
    raw = get_token_security(chain_id, contract_address)

    if not raw:
        return {"error": "Contract not found on GoPlus — may not be indexed yet"}

    def flag(key: str) -> bool:
        return raw.get(key) == "1"

    def pct(key: str) -> float:
        try:
            return float(raw.get(key) or 0)
        except (ValueError, TypeError):
            return 0.0

    return {
        "token_name": raw.get("token_name", "Unknown"),
        "token_symbol": raw.get("token_symbol", "Unknown"),
        # Source / ownership
        "is_open_source": flag("is_open_source"),
        "is_proxy": flag("is_proxy"),
        "hidden_owner": flag("hidden_owner"),
        "can_take_back_ownership": flag("can_take_back_ownership"),
        "selfdestruct": flag("selfdestruct"),
        "external_call": flag("external_call"),
        # Supply / mint
        "is_mintable": flag("is_mintable"),
        "owner_change_balance": flag("owner_change_balance"),
        # Trading restrictions
        "is_honeypot": flag("is_honeypot"),
        "is_blacklisted": flag("is_blacklisted"),
        "transfer_pausable": flag("transfer_pausable"),
        "cannot_buy": flag("cannot_buy"),
        "cannot_sell_all": flag("cannot_sell_all"),
        "slippage_modifiable": flag("slippage_modifiable"),
        "is_anti_whale": flag("is_anti_whale"),
        "anti_whale_modifiable": flag("anti_whale_modifiable"),
        "trading_cooldown": flag("trading_cooldown"),
        # Tax
        "buy_tax": pct("buy_tax"),
        "sell_tax": pct("sell_tax"),
        # Holder data (used by holder_analysis)
        "holder_count": int(raw.get("holder_count") or 0),
        "total_supply": raw.get("total_supply", "0"),
        "holders": raw.get("holders", []),
        "lp_holders": raw.get("lp_holders", []),
        "creators": raw.get("creators", []),
        "owners": raw.get("owners", []),
    }
