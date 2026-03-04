"""
Whale / smart money tracker — checks if a token appears in Binance's
smart money inflow ranking for the given period.
"""
from adapters.binance_web3 import get_inflow_rank


def get_whale_activity(chain_id: str, contract_address: str, period: str = "24h") -> dict:
    """
    Check if a contract is on the smart money radar.

    Args:
        chain_id: Numeric chain ID string.
        contract_address: Token contract address.
        period: "24h", "7d", or "30d"

    Returns:
        Dict with radar status and inflow stats if found.
    """
    try:
        rank_list = get_inflow_rank(chain_id, period)
    except ConnectionError as e:
        return {"error": str(e), "in_smart_money_radar": False}

    address_lower = contract_address.lower()
    match = next(
        (item for item in rank_list
         if item.get("ca", "").lower() == address_lower),
        None,
    )

    if match:
        return {
            "in_smart_money_radar": True,
            "net_inflow_usd": float(match.get("inflow") or 0),
            "buy_count": match.get("countBuy"),
            "sell_count": match.get("countSell"),
            "holders": match.get("holders"),
            "period": period,
        }

    return {
        "in_smart_money_radar": False,
        "period": period,
    }
