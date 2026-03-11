#!/usr/bin/env python3
"""
VeriTask 3.0 — DefiLlama TVL Scraper Skill
Fetches real-time TVL data from DefiLlama public API.

Usage:
    python defi_scraper.py [--protocol aave]
"""

import argparse
import json
import sys
from datetime import datetime, timezone

import requests

DEFILLAMA_TVL_URL = "https://api.llama.fi/tvl/{protocol}"
DEFAULT_PROTOCOL = "aave"


def fetch_tvl(protocol: str) -> dict:
    """
    Fetch current TVL for a protocol from DefiLlama.

    Returns:
        DataResult dict: {protocol, tvl_usd, fetched_at, source_url}
    Raises:
        RuntimeError on network or API errors.
    """
    url = DEFILLAMA_TVL_URL.format(protocol=protocol)
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"DefiLlama API request failed: {e}") from e

    # The /tvl/{protocol} endpoint returns a plain number (float)
    try:
        tvl_usd = float(resp.text)
    except ValueError as e:
        raise RuntimeError(
            f"Unexpected response from DefiLlama: {resp.text[:200]}"
        ) from e

    return {
        "protocol": protocol,
        "tvl_usd": tvl_usd,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source_url": url,
    }


def main():
    parser = argparse.ArgumentParser(description="Fetch protocol TVL from DefiLlama")
    parser.add_argument(
        "--protocol",
        default=DEFAULT_PROTOCOL,
        help=f"DefiLlama protocol slug (default: {DEFAULT_PROTOCOL})",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON (for machine consumption)",
    )
    args = parser.parse_args()

    print(f"\033[36m[Worker] 🌐 Fetching {args.protocol} TVL from DefiLlama...\033[0m")

    try:
        result = fetch_tvl(args.protocol)
    except RuntimeError as e:
        print(f"\033[31m[Worker] ❌ Error: {e}\033[0m", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(result))
    else:
        tvl_formatted = f"${result['tvl_usd']:,.2f}"
        print(f"\033[32m[Worker] ✅ {result['protocol'].upper()} TVL = {tvl_formatted}\033[0m")
        print(f"    Source: {result['source_url']}")
        print(f"    Time:   {result['fetched_at']}")


if __name__ == "__main__":
    main()
