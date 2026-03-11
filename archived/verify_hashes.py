#!/usr/bin/env python3
"""VeriTask Trust Layer Hash Verification Script"""
import json, hashlib

with open('archived/tmp_result.json', 'r') as f:
    pb = json.load(f)

print('=== VeriTask Trust Layer Hash Verification ===\n')

# 1) zkTLS hash = SHA256(json.dumps(data, sort_keys=True))
data_json = json.dumps(pb['data'], sort_keys=True)
computed_hash = hashlib.sha256(data_json.encode()).hexdigest()
stored_hash = pb['zk_proof']['hash']
print(f'[Layer 1] data JSON: {data_json}')
print(f'[Layer 1] SHA256(data):    {computed_hash}')
print(f'[Layer 1] zk_proof.hash:   {stored_hash}')
print(f'[Layer 1] Match: {computed_hash == stored_hash}\n')

# 2) tee_attestation.report_data == zk_proof.hash?
report_data = pb['tee_attestation']['report_data']
print(f'[Layer 2] tee_attestation.report_data: {report_data}')
print(f'[Layer 2] zk_proof.hash:               {stored_hash}')
print(f'[Layer 2] Match: {report_data == stored_hash}\n')

# 3) TDX Quote contains report_data?
quote_hex = pb['tee_attestation']['quote']
report_data_in_quote = report_data in quote_hex
print(f'[Layer 2] report_data found in TDX Quote hex: {report_data_in_quote}')
if report_data_in_quote:
    idx = quote_hex.index(report_data)
    print(f'[Layer 2] Position in Quote: char offset {idx} (byte ~{idx//2})')
print()

# 4) Reclaim attestor info
witnesses = pb['zk_proof']['proof']['witnesses']
print(f'[Layer 1] Reclaim attestor URL: {witnesses[0]["url"]}')
print(f'[Layer 1] Reclaim attestor ID:  {witnesses[0]["id"]}')
print()

# 5) Signatures
sigs = pb['zk_proof']['proof']['signatures']
print(f'[Layer 1] Signature count: {len(sigs)}')
print(f'[Layer 1] Signature[0]: {sigs[0][:66]}...')
print()

# 6) TDX event_log - app-id matches CVM?
event_log = json.loads(pb['tee_attestation']['event_log'])
app_id_entries = [e for e in event_log if e.get('event') == 'app-id']
print(f'[Layer 2] TDX event_log entries: {len(event_log)}')
if app_id_entries:
    app_id = app_id_entries[0]['event_payload']
    cvm_prefix = '2d29518d31fd53641b70a1754c79dce1450188b2'
    print(f'[Layer 2] app-id from TDX:    {app_id}')
    print(f'[Layer 2] CVM URL prefix:     {cvm_prefix}')
    print(f'[Layer 2] app-id matches CVM: {app_id == cvm_prefix}')
print()

# 7) claimData integrity
claim = pb['zk_proof']['proof']['claimData']
print(f'[Layer 1] claimData.provider: {claim["provider"]}')
print(f'[Layer 1] claimData.owner:    {claim["owner"]}')
print(f'[Layer 1] claimData.timestampS: {claim["timestampS"]}')
context = json.loads(claim['context'])
print(f'[Layer 1] extractedParameters.data: {context["extractedParameters"]["data"]}')
params = json.loads(claim['parameters'])
print(f'[Layer 1] parameters.url: {params["url"]}')
print()

print('=== Verification Complete ===')
