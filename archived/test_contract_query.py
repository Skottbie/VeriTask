#!/usr/bin/env python3
"""Query X Layer USDT contract for EIP-712 domain parameters."""
from web3 import Web3

w3 = Web3(Web3.HTTPProvider("https://rpc.xlayer.tech"))
print("Connected:", w3.is_connected())
print("ChainId:", w3.eth.chain_id)

contract = Web3.to_checksum_address("0x779ded0c9e1022225f8e0630b35a9b54be713736")

# name()
r = w3.eth.call({"to": contract, "data": "0x06fdde03"})
name = Web3.to_text(r[64 : 64 + Web3.to_int(r[32:64])])
print(f"name(): {repr(name)}")

# symbol()
r = w3.eth.call({"to": contract, "data": "0x95d89b41"})
sym = Web3.to_text(r[64 : 64 + Web3.to_int(r[32:64])])
print(f"symbol(): {repr(sym)}")

# decimals()
r = w3.eth.call({"to": contract, "data": "0x313ce567"})
print(f"decimals(): {Web3.to_int(r)}")

# version() - may or may not exist
try:
    r = w3.eth.call({"to": contract, "data": "0x54fd4d50"})
    ver = Web3.to_text(r[64 : 64 + Web3.to_int(r[32:64])])
    print(f"version(): {repr(ver)}")
except Exception as e:
    print(f"version(): NOT AVAILABLE ({e})")

# DOMAIN_SEPARATOR()
try:
    r = w3.eth.call({"to": contract, "data": "0x3644e515"})
    print(f"DOMAIN_SEPARATOR(): 0x{r.hex()}")
except Exception as e:
    print(f"DOMAIN_SEPARATOR(): NOT AVAILABLE ({e})")

# Check if contract supports receiveWithAuthorization/transferWithAuthorization
# transferWithAuthorization selector: 0xe3ee160e
# receiveWithAuthorization selector: 0xef55bec6
for fname, sel in [
    ("transferWithAuthorization", "0xe3ee160e"),
    ("receiveWithAuthorization", "0xef55bec6"),
]:
    try:
        # Call with dummy data to see if function exists (will revert but not with "function not found")
        r = w3.eth.call({"to": contract, "data": sel + "00" * 224})
        print(f"{fname}: EXISTS (returned data)")
    except Exception as e:
        err_str = str(e)
        if "execution reverted" in err_str.lower():
            print(f"{fname}: EXISTS (reverted, which means function is there)")
        else:
            print(f"{fname}: NOT FOUND ({err_str[:100]})")

# Also check the implementation address (it's a proxy)
# implementation() or getImplementation() 
# EIP-1967 implementation slot: 0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc
impl_slot = "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
storage = w3.eth.get_storage_at(contract, impl_slot)
impl_addr = "0x" + storage.hex()[-40:]
print(f"\nProxy implementation: {impl_addr}")

# Also check balanceOf for our wallet
from_addr = "0x012e6cfbbd1fcf5751d08ec2919d1c7873a4bb85"
# balanceOf(address) = 0x70a08231
call_data = "0x70a08231" + "0" * 24 + from_addr[2:]
r = w3.eth.call({"to": contract, "data": call_data})
balance = Web3.to_int(r)
print(f"\nUSDT balance of {from_addr}: {balance} ({balance / 1e6} USDT)")
