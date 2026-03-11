import json

with open(r"D:\VeriTask\session_v348.jsonl", encoding="utf-8") as f:
    lines = f.readlines()

# L46 (1-indexed) = index 45
msg46 = json.loads(lines[45])
print("=== L46 ===")
print("role:", msg46.get("role"))
prov = msg46.get("provenance", {})
print("provenance:", json.dumps(prov, indent=2, ensure_ascii=False))

text = ""
for p in msg46.get("parts", []):
    if p.get("type") == "text":
        text += p["text"]
print(f"\ntext ({len(text)}ch):")
print(text[:1000])

# Also check L44 for comparison
print("\n\n=== L44 ===")
msg44 = json.loads(lines[43])
print("role:", msg44.get("role"))
text44 = ""
for p in msg44.get("parts", []):
    if p.get("type") == "text":
        text44 += p["text"]
print(f"text ({len(text44)}ch):")
print(text44[:500])
