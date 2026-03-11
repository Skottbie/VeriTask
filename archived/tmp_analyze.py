import json

d = json.load(open('D:/VeriTask/tmp_result.json'))
zk = d['zk_proof']
print('=== ZK PROOF ===')
print('type:', zk['type'])
print()

proof = zk['proof']
cd = proof.get('claimData', {})
print('--- claimData ---')
for k, v in cd.items():
    val = str(v)
    if len(val) > 150:
        val = val[:150] + '...'
    print(f'  {k}: {val}')
print()

print('--- identifier ---')
ident = str(proof.get('identifier', ''))
print(f'  {ident[:100]}')
print()

sigs = proof.get('signatures', [])
print('--- signatures ---')
print(f'  count: {len(sigs)}')
for s in sigs[:3]:
    print(f'  {str(s)[:120]}...')
print()

wit = proof.get('witnesses', [])
print('--- witnesses ---')
print(f'  count: {len(wit)}')
for w in wit[:3]:
    print(f'  {str(w)[:150]}...')
print()

rb = zk.get('response_body', '')
print('--- response_body ---')
print(f'  value: {str(rb)[:100]}')
print(f'  length: {len(str(rb))}')
print()

# Check claimData.context for app id 
ctx = cd.get('context', '')
print('--- context (parsed) ---')
try:
    ctx_obj = json.loads(ctx) if isinstance(ctx, str) else ctx
    for k, v in ctx_obj.items():
        print(f'  {k}: {str(v)[:100]}')
except:
    print(f'  raw: {str(ctx)[:200]}')
print()

# Check claimData.parameters
params = cd.get('parameters', '')
print('--- parameters (parsed) ---')
try:
    params_obj = json.loads(params) if isinstance(params, str) else params
    for k, v in params_obj.items():
        print(f'  {k}: {str(v)[:100]}')
except:
    print(f'  raw: {str(params)[:200]}')
print()

print('--- timestampS ---')
ts = cd.get('timestampS', '')
print(f'  {ts}')
import datetime
try:
    dt = datetime.datetime.fromtimestamp(int(ts), tz=datetime.timezone.utc)
    print(f'  = {dt.isoformat()}')
except:
    pass
print()

print('--- owner ---')
print(f'  {cd.get("owner", "")}')
print()

print('--- epoch ---')
print(f'  {cd.get("epoch", "")}')
