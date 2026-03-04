# Token Safety Scanner

A CLI tool and AI skill that analyzes EVM token contracts for rug pull risks, honeypots, holder concentration, and smart money activity. Generates a 0-100 risk score with detailed flags.

Works with **Binance Web3**, **OKX**, **OpenClaw**, and any AI agent platform that supports CLI skills.

---

## Quick Start

```bash
pip install requests

# Scan by contract address
python main.py --address 0x6982508145454ce325ddbe47a25d4ec3d2311933 --chain eth

# Scan by token name (auto-resolves address)
python main.py --token PEPE --chain eth

# JSON output for downstream processing
python main.py --address 0x... --chain bsc --json
```

**Example output:**

```
========================================================
  TOKEN SAFETY REPORT
  Pepe (PEPE)
  0x69825081...311933  [ETH]
========================================================

  Score : 92/100  [##################--]  SAFE

  ------------------------------------------------------
  CONTRACT AUDIT
  ------------------------------------------------------
  Open Source      : [ OK ] Verified
  Honeypot         : [ OK ] No
  Mintable         : [ OK ] No
  Blacklist        : [!!] YES
  Buy Tax          : 0.0%
  Sell Tax         : 0.0%

  ------------------------------------------------------
  HOLDER ANALYSIS
  ------------------------------------------------------
  Total Holders    : 508,775
  Top 10 Hold      : 41.5%
  Insider Hold     : 0.0%
  LP Locked        : [ OK ] Yes

  ------------------------------------------------------
  FLAGS
  ------------------------------------------------------
  [!] Blacklist function exists
========================================================
```

---

## Supported Chains

| Flag | Chain | Chain ID |
|------|-------|----------|
| `eth` | Ethereum | 1 |
| `bsc` | BNB Smart Chain | 56 |
| `polygon` | Polygon | 137 |
| `arbitrum` | Arbitrum One | 42161 |
| `base` | Base | 8453 |
| `avax` | Avalanche | 43114 |
| `op` | Optimism | 10 |

---

## What It Checks

### Contract Audit (via GoPlus Security API)
- Honeypot detection
- Source code verified / open source
- Mintable supply (owner can print tokens)
- Hidden owner / ownership backdoor
- Transfer pause function
- Blacklist / whitelist controls
- Buy and sell tax rates
- Selfdestruct function
- Cannot sell all tokens

### Holder Analysis (via GoPlus)
- Total holder count
- Top 10 holder concentration %
- Insider / dev wallet holdings %
- LP locked status

### Smart Money Radar (via Binance Web3 API)
- Whether the token appears in Binance's smart money inflow ranking
- 24h net inflow USD
- Buy / sell transaction counts from tracked wallets

### Risk Score
| Score | Rating | Meaning |
|-------|--------|---------|
| 80-100 | SAFE | Low risk |
| 60-79 | CAUTION | Some risks, proceed carefully |
| 40-59 | RISKY | Multiple flags, high caution |
| 0-39 | DANGER | Severe risks — honeypot or scam likely |

---

## Architecture

```
token-safety-scanner/
├── adapters/
│   ├── goplus.py          # GoPlus Security API (free, no auth)
│   └── binance_web3.py    # Binance Web3 public API (free, no auth)
├── scanner/
│   ├── contract_audit.py  # Parses GoPlus data into structured audit
│   ├── holder_analysis.py # Concentration analysis from audit data
│   ├── whale_tracker.py   # Smart money inflow via Binance
│   └── risk_scorer.py     # Pure calculation, no API calls
├── main.py                # CLI entry point
├── SKILL.md               # AI agent skill definition
└── tests/
    └── test_scanner.py
```

Data flow: `main.py` resolves address → calls `contract_audit` (GoPlus) → `holder_analysis` (from audit data) → `whale_tracker` (Binance) → `risk_scorer` (pure calc) → formats report.

---

## Data Sources

| Source | Auth Required | Chains | Used For |
|--------|--------------|--------|----------|
| [GoPlus Security](https://gopluslabs.io/) | None | 30+ | Contract audit, holder data |
| [Binance Web3 API](https://web3.binance.com/) | None | ETH, BSC | Token search, smart money inflow |

No API keys needed to run this tool.

---

## Running Tests

```bash
pip install pytest
python -m pytest tests/ -v
```

Tests use USDT on BSC as a known-safe token baseline.

---

## Use as an AI Skill

This tool is designed to be called by AI agents. See [SKILL.md](./SKILL.md) for the full skill definition compatible with Binance Skills Hub.

The `--json` flag produces structured output suitable for agent consumption:

```bash
python main.py --address 0x... --chain bsc --json
```

```json
{
  "address": "0x...",
  "chain": "bsc",
  "audit": { "is_honeypot": false, "buy_tax": 0.0, ... },
  "holders": { "top10_concentration_pct": 26.8, ... },
  "risk": { "score": 80, "rating": "SAFE", "flags": [...] }
}
```

---

## Disclaimer

This tool is for informational purposes only. Data is sourced from third-party APIs and may be incomplete or inaccurate. This does not constitute financial or investment advice. Always do your own research (DYOR).

---

## License

MIT
