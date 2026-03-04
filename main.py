#!/usr/bin/env python3
"""
Token Safety Scanner — CLI entry point.

Usage:
  python main.py --address 0x... --chain bsc
  python main.py --token PEPE --chain eth
  python main.py --address 0x... --chain bsc --json
"""
import argparse
import json
import sys

from adapters.binance_web3 import search_token
from scanner.contract_audit import audit_contract
from scanner.holder_analysis import analyze_holders
from scanner.risk_scorer import score
from scanner.whale_tracker import get_whale_activity

CHAIN_MAP = {
    "eth": "1",
    "bsc": "56",
    "polygon": "137",
    "arbitrum": "42161",
    "base": "8453",
    "avax": "43114",
    "op": "10",
}


def resolve_address(token_input: str, chain_id: str) -> str:
    """If input is not a 0x address, search Binance Web3 to resolve it."""
    if token_input.startswith("0x") and len(token_input) == 42:
        return token_input

    print(f"Searching for token: {token_input}...")
    try:
        results = search_token(token_input)
    except ConnectionError as e:
        print(f"Search failed: {e}")
        sys.exit(1)

    if not results:
        print("Token not found via Binance Web3 search.")
        sys.exit(1)

    # Prefer a result on the requested chain
    for r in results:
        if str(r.get("chainId")) == chain_id:
            addr = r.get("contractAddress") or r.get("address")
            if addr:
                print(f"Found: {r.get('name')} ({r.get('symbol')}) on chain {chain_id}")
                return addr

    # Fallback: first EVM result (filter out Solana / Tron non-0x addresses)
    for r in results:
        addr = r.get("contractAddress", "")
        if addr.startswith("0x"):
            found_chain = r.get("chainId", "?")
            print(f"Found: {r.get('name')} ({r.get('symbol')}) on chain {found_chain} (you requested {chain_id})")
            return addr

    print(f"No EVM contract found for '{token_input}' — only non-EVM results returned.")
    sys.exit(1)


def _bar(score_val: int, width: int = 20) -> str:
    filled = score_val * width // 100
    return "#" * filled + "-" * (width - filled)


def format_report(address: str, chain: str, audit: dict, holders: dict, whale: dict, risk: dict) -> str:
    lines = []
    SEP = "-" * 54

    lines.append("=" * 56)
    lines.append("  TOKEN SAFETY REPORT")
    lines.append(f"  {audit.get('token_name')} ({audit.get('token_symbol')})")
    lines.append(f"  {address[:10]}...{address[-6:]}  [{chain.upper()}]")
    lines.append("=" * 56)

    # Risk score
    s = risk["score"]
    lines.append(f"\n  Score : {s}/100  [{_bar(s)}]  {risk['rating']}")

    # Contract audit
    lines.append(f"\n  {SEP}")
    lines.append("  CONTRACT AUDIT")
    lines.append(f"  {SEP}")

    def yn(val: bool, danger_if_true: bool = True) -> str:
        if val:
            return "[!!] YES" if danger_if_true else "[ OK ] YES"
        return "[ OK ] No" if danger_if_true else "[!!] No"

    lines.append(f"  Open Source      : {yn(not audit.get('is_open_source'), danger_if_true=False) if not audit.get('is_open_source') else '[ OK ] Verified'}")
    lines.append(f"  Honeypot         : {yn(audit.get('is_honeypot'))}")
    lines.append(f"  Mintable         : {yn(audit.get('is_mintable'))}")
    lines.append(f"  Hidden Owner     : {yn(audit.get('hidden_owner'))}")
    lines.append(f"  Blacklist        : {yn(audit.get('is_blacklisted'))}")
    lines.append(f"  Pause Transfers  : {yn(audit.get('transfer_pausable'))}")
    lines.append(f"  Can't Sell All   : {yn(audit.get('cannot_sell_all'))}")
    lines.append(f"  Buy Tax          : {audit.get('buy_tax', 0):.1f}%")
    lines.append(f"  Sell Tax         : {audit.get('sell_tax', 0):.1f}%")

    # Holder analysis
    lines.append(f"\n  {SEP}")
    lines.append("  HOLDER ANALYSIS")
    lines.append(f"  {SEP}")
    if "error" in holders:
        lines.append(f"  {holders['error']}")
    else:
        lines.append(f"  Total Holders    : {holders.get('holder_count', 'N/A'):,}")
        lines.append(f"  Top 10 Hold      : {holders.get('top10_concentration_pct', 0):.1f}%")
        lines.append(f"  Insider Hold     : {holders.get('insider_holdings_pct', 0):.1f}%")
        lines.append(f"  LP Locked        : {'[ OK ] Yes' if holders.get('lp_locked') else '[!!] No / Unknown'}")

    # Whale activity
    lines.append(f"\n  {SEP}")
    lines.append("  WHALE / SMART MONEY (Binance Web3)")
    lines.append(f"  {SEP}")
    if whale.get("error"):
        lines.append(f"  {whale['error']}")
    elif whale.get("in_smart_money_radar"):
        lines.append(f"  On Radar         : [ OK ] YES")
        lines.append(f"  Net Inflow 24h   : ${whale.get('net_inflow_usd', 0):,.0f}")
        lines.append(f"  Buys / Sells     : {whale.get('buy_count')} / {whale.get('sell_count')}")
    else:
        lines.append("  On Radar         : Not in top smart money inflow list")

    # Flags
    if risk["flags"]:
        lines.append(f"\n  {SEP}")
        lines.append("  FLAGS")
        lines.append(f"  {SEP}")
        for flag in risk["flags"]:
            lines.append(f"  [!] {flag}")

    lines.append("\n" + "=" * 56)
    lines.append("  [!] For reference only. Not financial advice.")
    lines.append("=" * 56)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Token Safety Scanner")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--address", "-a", help="Contract address (0x...)")
    group.add_argument("--token", "-t", help="Token name or symbol to search")
    parser.add_argument(
        "--chain", "-c",
        default="bsc",
        choices=list(CHAIN_MAP.keys()),
        help="Chain to scan (default: bsc)",
    )
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of formatted report")
    args = parser.parse_args()

    chain_id = CHAIN_MAP[args.chain]
    token_input = args.address or args.token

    address = resolve_address(token_input, chain_id)
    print(f"Scanning {address} on {args.chain.upper()}...\n")

    try:
        audit = audit_contract(chain_id, address)
    except ConnectionError as e:
        print(f"Error: {e}")
        sys.exit(1)

    if "error" in audit:
        print(f"Contract audit failed: {audit['error']}")
        sys.exit(1)

    holders = analyze_holders(audit)
    whale = get_whale_activity(chain_id, address)
    risk = score(audit, holders, whale)

    if args.json:
        output = {
            "address": address,
            "chain": args.chain,
            "audit": {k: v for k, v in audit.items() if k not in ("holders", "lp_holders", "creators", "owners")},
            "holders": holders,
            "whale": whale,
            "risk": risk,
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print(format_report(address, args.chain, audit, holders, whale, risk))


if __name__ == "__main__":
    main()
