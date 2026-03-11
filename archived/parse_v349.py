#!/usr/bin/env python3
"""Parse v3.4.9 session - analyze all issues"""
import json, shutil

# Copy files to local
src_main = r"\\wsl$\Ubuntu\home\skottbie\.openclaw\agents\main\sessions\9d9a9e03-9434-4061-aeb7-dda7b45afac0.jsonl"
src_pro = r"\\wsl$\Ubuntu\home\skottbie\.openclaw\agents\pro\sessions\a478421c-7421-4f0c-9d4c-78fe0c7854d9.jsonl"

shutil.copy2(src_main, "session_v349.jsonl")
shutil.copy2(src_pro, "session_v349_pro.jsonl")

with open("session_v349.jsonl", "r", encoding="utf-8") as f:
    lines = f.readlines()

print(f"=== v3.4.9 Main Session: {len(lines)} lines ===\n")

for i, raw in enumerate(lines, 1):
    try:
        obj = json.loads(raw.strip())
        msg = obj.get("message", {})
        role = msg.get("role", "?")
        
        # Get text content
        content = msg.get("content", [])
        text = ""
        tool_calls = []
        for c in content:
            if isinstance(c, dict):
                if c.get("type") == "text":
                    text += c["text"]
                elif c.get("type") == "tool_use":
                    tool_calls.append(c.get("name", "?"))
        
        # Get provenance
        prov = msg.get("provenance", {})
        prov_kind = prov.get("kind", "")
        prov_tool = prov.get("sourceTool", "")
        
        # Summarize
        if role == "user":
            prov_str = f" [{prov_kind}:{prov_tool}]" if prov_kind else ""
            preview = text[:150].replace('\n', '\\n')
            print(f"L{i:02d} USER{prov_str}: ({len(text)}ch) {preview}")
        elif role == "assistant":
            if tool_calls:
                print(f"L{i:02d} ASST: TOOL({', '.join(tool_calls)})")
            elif text:
                # Check for key patterns
                flags = []
                if "Step 0a" in text: flags.append("STEP_0A")
                if "Step 0b" in text: flags.append("STEP_0B")
                if "Step 0c" in text or "兑换" in text: flags.append("STEP_0C")
                if "Step 1" in text: flags.append("STEP_1")
                if "Step 2" in text: flags.append("STEP_2")
                if "Step 3" in text: flags.append("STEP_3")
                if "Step 4" in text: flags.append("STEP_4")
                if "Step 5" in text: flags.append("STEP_5")
                if "Step 6" in text: flags.append("STEP_6")
                if "already_handled" in text: flags.append("ALREADY_HANDLED")
                if "分析中" in text: flags.append("PLACEHOLDER")
                if "json" in text.lower() or '{"' in text: flags.append("HAS_JSON")
                if "[{" in text: flags.append("RAW_JSON_ARRAY")
                
                flag_str = " | ".join(flags) if flags else ""
                preview = text[:150].replace('\n', '\\n')
                print(f"L{i:02d} ASST: ({len(text)}ch) [{flag_str}] {preview}")
            else:
                print(f"L{i:02d} ASST: (empty)")
        elif role == "toolResult":
            # Just note it
            tool_name = ""
            for c in content:
                if isinstance(c, dict) and "toolName" in c:
                    tool_name = c["toolName"]
            result_text = ""
            for c in content:
                if isinstance(c, dict) and c.get("type") == "text":
                    result_text += c.get("text", "")
            preview = result_text[:100].replace('\n', '\\n') if result_text else "(no text)"
            print(f"L{i:02d} TOOL_RESULT({tool_name}): {preview}")
        else:
            otype = obj.get("type", "?")
            print(f"L{i:02d} {role}/{otype}")
    except Exception as e:
        print(f"L{i:02d} ERROR: {e}")
