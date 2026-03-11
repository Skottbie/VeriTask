#!/usr/bin/env python3
try:
    from eth_account import Account
    print("eth_account: OK")
except ImportError:
    print("eth_account: MISSING")

try:
    import requests
    print("requests: OK")
except ImportError:
    print("requests: MISSING")

try:
    from dotenv import load_dotenv
    print("dotenv: OK")
except ImportError:
    print("dotenv: MISSING")
