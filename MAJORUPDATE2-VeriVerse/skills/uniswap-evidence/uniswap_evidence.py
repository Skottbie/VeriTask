#!/usr/bin/env python3
"""uniswap_evidence.py - extract swap route evidence from onchainos quote output.

This script is an evidence layer for review flows: it does not execute swaps.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
VERITASK_ROOT = ROOT_DIR.parent

for env_path in [
    Path("/home/skottbie/.openclaw/.env"),
    Path("/home/skottbie/.openclaw/workspace/.env"),
    ROOT_DIR / ".env",
    VERITASK_ROOT / ".env",
]:
    if env_path.exists():
        load_dotenv(env_path)

ONCHAINOS_BIN = os.getenv("ONCHAINOS_BIN", os.path.expanduser("~/.local/bin/onchainos"))

SOURCE_KEYS = {
    "dex",
    "dexname",
    "source",
    "sourcename",
    "protocol",
    "protocolname",
    "router",
    "routername",
    "liquiditysource",
    "provider",
    "providername",
}

UNISWAP_PATTERNS = [
    re.compile(r"\\buniswap\\b", re.IGNORECASE),
    re.compile(r"\\buniswap\\s*v[23]\\b", re.IGNORECASE),
    re.compile(r"\\buni\\s*v[23]\\b", re.IGNORECASE),
]


def _run_onchainos_json(args: list[str], timeout: int = 45) -> Any:
    cmd = [ONCHAINOS_BIN] + args
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        stdout = (proc.stdout or "").strip()
        detail = stderr or stdout or f"exit {proc.returncode}"
        raise RuntimeError(f"onchainos command failed: {detail}")

    raw = (proc.stdout or "").strip()
    if not raw:
        raise RuntimeError("onchainos returned empty stdout")

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"onchainos returned invalid JSON: {raw[:300]}") from exc


def _extract_first_item(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, dict):
            return data
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    return item
        return payload

    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                return item

    return {}


def _collect_protocol_mentions(node: Any, path: str, out: list[dict[str, str]]) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            key_str = str(key)
            child_path = f"{path}.{key_str}"
            normalized_key = key_str.strip().lower()

            if isinstance(value, str) and normalized_key in SOURCE_KEYS:
                val = value.strip()
                if val:
                    out.append({"path": child_path, "value": val})

            _collect_protocol_mentions(value, child_path, out)

    elif isinstance(node, list):
        for idx, item in enumerate(node):
            _collect_protocol_mentions(item, f"{path}[{idx}]", out)


def _normalize_unique(values: list[str]) -> list[str]:
    seen: dict[str, str] = {}
    for value in values:
        key = value.strip().lower()
        if key and key not in seen:
            seen[key] = value.strip()
    return list(seen.values())


def _is_uniswap_source(name: str) -> bool:
    return any(pattern.search(name) for pattern in UNISWAP_PATTERNS)


def build_route_evidence(quote_payload: Any) -> dict[str, Any]:
    mentions: list[dict[str, str]] = []
    _collect_protocol_mentions(quote_payload, "$", mentions)

    sources = _normalize_unique([item["value"] for item in mentions])
    uniswap_matches = [source for source in sources if _is_uniswap_source(source)]

    first = _extract_first_item(quote_payload)
    quote_summary = {
        "fromTokenAmount": first.get("fromTokenAmount"),
        "toTokenAmount": first.get("toTokenAmount"),
        "priceImpactPercent": first.get("priceImpactPercent"),
        "gasFee": first.get("gasFee"),
        "estimatedOutUsd": first.get("toTokenValue"),
    }

    return {
        "routeSources": sources,
        "routeSourceMentions": mentions,
        "containsUniswap": len(uniswap_matches) > 0,
        "uniswapMatches": uniswap_matches,
        "quoteSummary": quote_summary,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract Uniswap route evidence from onchainos quote")
    parser.add_argument("--from-token", required=True, help="From token contract address")
    parser.add_argument("--to-token", required=True, help="To token contract address")
    parser.add_argument("--amount", required=True, help="Amount in token minimal units")
    parser.add_argument("--chain", default="xlayer", help="Chain name for onchainos swap quote")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()

    try:
        quote_payload = _run_onchainos_json(
            [
                "swap",
                "quote",
                "--from",
                args.from_token,
                "--to",
                args.to_token,
                "--amount",
                args.amount,
                "--chain",
                args.chain,
            ]
        )

        evidence = build_route_evidence(quote_payload)
        result = {
            "success": True,
            "mode": "route-evidence",
            "chain": args.chain,
            "fromToken": args.from_token,
            "toToken": args.to_token,
            "amount": args.amount,
            "routeEvidence": evidence,
        }

        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        else:
            verdict = "FOUND" if evidence["containsUniswap"] else "NOT_FOUND"
            print(f"Uniswap evidence: {verdict}")
            print(f"Sources: {', '.join(evidence['routeSources']) or 'N/A'}")

    except Exception as exc:
        out = {"success": False, "error": str(exc)}
        if args.json:
            print(json.dumps(out, indent=2, ensure_ascii=False))
        else:
            print(f"Route evidence failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
