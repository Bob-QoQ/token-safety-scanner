"""
GoPlus Security API adapter.
Free, no auth required, supports 30+ chains.
Docs: https://docs.gopluslabs.io/
"""
import requests
from typing import Optional

GOPLUS_BASE_URL = "https://api.gopluslabs.io/api/v1"

# GoPlus numeric chain IDs
CHAIN_IDS = {
    "eth": "1",
    "bsc": "56",
    "polygon": "137",
    "arbitrum": "42161",
    "base": "8453",
    "avax": "43114",
    "op": "10",
}


def get_token_security(chain_id: str, contract_address: str) -> Optional[dict]:
    """
    Fetch token security data from GoPlus Security API.

    Args:
        chain_id: Numeric chain ID (e.g. "1" for ETH, "56" for BSC)
        contract_address: Token contract address (0x...)

    Returns:
        Dict with security fields, or None if not found.

    Raises:
        ConnectionError: On network or API errors.
    """
    url = f"{GOPLUS_BASE_URL}/token_security/{chain_id}"
    params = {"contract_addresses": contract_address.lower()}

    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        raise ConnectionError(f"GoPlus API error: {e}")

    if data.get("code") != 1:
        raise ConnectionError(f"GoPlus returned error code: {data.get('code')} — {data.get('message')}")

    result = data.get("result", {})
    return result.get(contract_address.lower())
