import json

with open(r"D:\VeriTask\session_v348.jsonl", encoding="utf-8") as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}")

# Check L44, L45, L46 raw structure
for idx in [43, 44, 45]:
    line = lines[idx].strip()
    try:
        obj = json.loads(line)
        keys = list(obj.keys())
        role = obj.get("role", obj.get("type", "N/A"))
        print(f"\nL{idx+1}: keys={keys[:8]}, role/type={role}")
        
        # Try different content access patterns
        if "parts" in obj:
            for i, p in enumerate(obj["parts"][:3]):
                ptype = p.get("type", "?")
                text = p.get("text", "")[:200]
                print(f"  part[{i}] type={ptype}: {text[:200]}")
        elif "content" in obj:
            content = obj["content"]
            if isinstance(content, str):
                print(f"  content: {content[:300]}")
            elif isinstance(content, list):
                for i, c in enumerate(content[:3]):
                    print(f"  content[{i}]: {str(c)[:200]}")
        elif "text" in obj:
            print(f"  text: {obj['text'][:300]}")
        elif "message" in obj:
            msg = obj["message"]
            if isinstance(msg, dict):
                mrole = msg.get("role", "?")
                print(f"  message.role={mrole}")
                if "parts" in msg:
                    for i, p in enumerate(msg["parts"][:3]):
                        ptype = p.get("type", "?")
                        text = p.get("text", "")[:200]
                        print(f"  msg.part[{i}] type={ptype}: {text[:200]}")
                elif "content" in msg:
                    print(f"  msg.content: {str(msg['content'])[:300]}")
    except Exception as e:
        print(f"\nL{idx+1}: ERROR: {e}")
        print(f"  raw: {line[:200]}")
