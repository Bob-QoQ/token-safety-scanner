"""
Basic smoke tests — use known real tokens to validate API responses.
Run: python -m pytest tests/ -v
"""
import pytest
from scanner.contract_audit import audit_contract
from scanner.holder_analysis import analyze_holders
from scanner.risk_scorer import score
from scanner.whale_tracker import get_whale_activity

# USDT on BSC (well-known, should be safe)
USDT_BSC = "0x55d398326f99059ff775485246999027b3197955"
BSC_CHAIN_ID = "56"

# Known honeypot example (for manual testing only, skip in CI)
# HONEYPOT_ADDR = "0x..."


class TestContractAudit:
    def test_usdt_bsc_is_open_source(self):
        audit = audit_contract(BSC_CHAIN_ID, USDT_BSC)
        assert "error" not in audit
        assert audit["is_open_source"] is True

    def test_usdt_bsc_not_honeypot(self):
        audit = audit_contract(BSC_CHAIN_ID, USDT_BSC)
        assert audit["is_honeypot"] is False

    def test_returns_token_name(self):
        audit = audit_contract(BSC_CHAIN_ID, USDT_BSC)
        assert audit["token_symbol"].upper() in ("USDT", "BSC-USD")


class TestHolderAnalysis:
    def test_holder_analysis_structure(self):
        audit = audit_contract(BSC_CHAIN_ID, USDT_BSC)
        holders = analyze_holders(audit)
        assert "error" not in holders or "holder_count" in holders

    def test_concentration_is_percentage(self):
        audit = audit_contract(BSC_CHAIN_ID, USDT_BSC)
        holders = analyze_holders(audit)
        if "error" not in holders:
            assert 0 <= holders["top10_concentration_pct"] <= 100


class TestRiskScorer:
    def test_safe_token_scores_above_50(self):
        audit = audit_contract(BSC_CHAIN_ID, USDT_BSC)
        holders = analyze_holders(audit)
        whale = {"in_smart_money_radar": False, "period": "24h"}
        result = score(audit, holders, whale)
        assert result["score"] >= 50
        assert result["rating"] in ("SAFE", "CAUTION", "RISKY", "DANGER")

    def test_honeypot_scores_low(self):
        fake_audit = {
            "is_open_source": False,
            "is_honeypot": True,
            "is_mintable": True,
            "hidden_owner": True,
            "buy_tax": 0,
            "sell_tax": 0,
            "transfer_pausable": False,
            "is_blacklisted": False,
            "cannot_sell_all": False,
            "slippage_modifiable": False,
            "can_take_back_ownership": False,
            "selfdestruct": False,
            "owner_change_balance": False,
        }
        result = score(fake_audit, {"error": "no data"}, {"in_smart_money_radar": False})
        assert result["score"] <= 20
        assert result["rating"] == "DANGER"
