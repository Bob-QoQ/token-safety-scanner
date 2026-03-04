"""
Binance Web3 public API adapter.
Free, no auth required.
"""
import requests
from typing import Optional

BINANCE_WEB3_BASE = "https://web3.binance.com/bapi/defi"


def search_token(keyword: str) -> list:
    """
    Search for a token by name or symbol.

    Returns:
        List of token result dicts, empty list if none found.
    """
    url = f"{BINANCE_WEB3_BASE}/v5/public/wallet-direct/buw/wallet/market/token/search"
    params = {"keyword": keyword}

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        result = data.get("data", [])
        return result if isinstance(result, list) else []
    except requests.RequestException as e:
        raise ConnectionError(f"Binance Web3 search error: {e}")


def get_token_info(chain_id: str, contract_address: str) -> Optional[dict]:
    """
    Fetch token metadata and market info.

    Returns:
        Dict with token info, or None if not found.
    """
    url = f"{BINANCE_WEB3_BASE}/v1/public/wallet-direct/buw/wallet/dex/market/token/meta/info"
    params = {
        "chainId": chain_id,
        "contractAddress": contract_address,
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data")
    except requests.RequestException as e:
        raise ConnectionError(f"Binance Web3 token info error: {e}")


def get_inflow_rank(chain_id: str, period: str = "24h") -> list:
    """
    Fetch smart money inflow ranking for a chain.

    Args:
        chain_id: Numeric chain ID string.
        period: "24h", "7d", "30d"

    Returns:
        List of ranked token inflow dicts.
    """
    url = f"{BINANCE_WEB3_BASE}/v1/public/wallet-direct/tracker/wallet/token/inflow/rank/query"
    payload = {
        "chainId": chain_id,
        "period": period,
        "tagType": 2,  # smart money wallets
    }

    try:
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        result = data.get("data", [])
        return result if isinstance(result, list) else []
    except requests.RequestException as e:
        raise ConnectionError(f"Binance Web3 inflow rank error: {e}")
