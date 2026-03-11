#!/usr/bin/env python3
"""
Reverse-engineer the correct EIP-712 domain by matching DOMAIN_SEPARATOR.
Known: DOMAIN_SEPARATOR = 0xd591d9baf744328d9400b923cb02c9474d367d591ca1ab24d8c4068be527599d
Known: name() = 'USD₮0', version() = N/A, chainId = 196, contract = 0x779...
"""
from eth_abi import encode
from web3 import Web3

TARGET_DS = "0xd591d9baf744328d9400b923cb02c9474d367d591ca1ab24d8c4068be527599d"

# EIP-712 domain separator type hash
# keccak256("EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)")
EIP712_DOMAIN_TYPEHASH = Web3.keccak(
    text="EIP712Domain(string name,string version,uint256 chainId,address verifyingContract)"
)
print(f"EIP712Domain typehash: 0x{EIP712_DOMAIN_TYPEHASH.hex()}")

contract = Web3.to_checksum_address("0x779ded0c9e1022225f8e0630b35a9b54be713736")
chain_id = 196

# Try different name + version combinations
candidates = [
    ("USD₮0", "1"),
    ("USD₮0", "2"),
    ("Tether USD", "1"),
    ("Tether USD", "2"),
    ("TetherToken", "1"),
    ("TetherToken", "2"),
    ("USDT", "1"),
    ("USDT", "2"),
    ("USD₮0", ""),
    # Some contracts use the symbol
    ("USD₮", "1"),
    ("USD₮", "2"),
]

for name, version in candidates:
    name_hash = Web3.keccak(text=name)
    version_hash = Web3.keccak(text=version)
    
    ds = Web3.keccak(
        EIP712_DOMAIN_TYPEHASH
        + name_hash
        + version_hash
        + chain_id.to_bytes(32, "big")
        + bytes(12) + bytes.fromhex(contract[2:])
    )
    match = "✅ MATCH!" if ("0x" + ds.hex()) == TARGET_DS else "❌"
    print(f"  name={repr(name):20s} version={repr(version):5s} → 0x{ds.hex()[:16]}... {match}")
