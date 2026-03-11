import json

with open(r"D:\VeriTask\session_v348.jsonl", encoding="utf-8") as f:
    lines = f.readlines()

# L45 (1-indexed) = index 44
msg45 = json.loads(lines[44])
msg = msg45.get("message", {})
content = msg.get("content", [])
full_text = ""
for c in content:
    if isinstance(c, dict) and c.get("type") == "text":
        full_text += c["text"]
    elif isinstance(c, str):
        full_text += c

print(f"L45 full text ({len(full_text)} chars):")
print("=" * 80)
print(full_text)
print("=" * 80)

# Also check L46 full text
msg46 = json.loads(lines[45])
msg46m = msg46.get("message", {})
content46 = msg46m.get("content", [])
full_text46 = ""
for c in content46:
    if isinstance(c, dict) and c.get("type") == "text":
        full_text46 += c["text"]
    elif isinstance(c, str):
        full_text46 += c

print(f"\nL46 full text ({len(full_text46)} chars):")
print("=" * 80)
print(full_text46)
print("=" * 80)
