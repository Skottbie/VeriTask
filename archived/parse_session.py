#!/usr/bin/env python3
"""Parse session_spark_1128_pro_thinking.jsonl and extract full thinking timeline."""
import json
import sys
from datetime import datetime, timedelta, timezone

UTC = timezone.utc
GMT8 = timezone(timedelta(hours=8))

def ts_to_gmt8(ts_str):
    if not ts_str:
        return "??:??:??"
    try:
        ts_str = ts_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        dt_gmt8 = dt.astimezone(GMT8)
        return dt_gmt8.strftime("%H:%M:%S")
    except Exception as e:
        return f"ERR({e})"

def truncate(s, max_len=200):
    if not s:
        return ""
    s = str(s)
    if len(s) <= max_len:
        return s
    return s[:max_len] + f"... [{len(s)} chars total]"

def extract_content_parts(content):
    if isinstance(content, str):
        return [("text", content)]
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                t = item.get("type", "unknown")
                if t == "text":
                    parts.append(("text", item.get("text", "")))
                elif t in ("thinking", "thought"):
                    parts.append(("thinking", item.get("thinking", item.get("thought", item.get("text", "")))))
                elif t == "tool_use":
                    name = item.get("name", "?")
                    inp = item.get("input", {})
                    parts.append(("tool_use", f"{name} | {json.dumps(inp, ensure_ascii=False)}"))
                elif t == "tool_result":
                    parts.append(("tool_result", item.get("content", item.get("output", ""))))
                else:
                    parts.append((t, json.dumps(item, ensure_ascii=False)))
            elif isinstance(item, str):
                parts.append(("text", item))
        return parts
    return [("raw", str(content))]

def main():
    filepath = r'd:\VeriTask\archived\session_spark_1128_pro_thinking.jsonl'
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    output = []
    output.append(f"=== VeriTask Pro Session Timeline ({len(lines)} lines) ===\n")
    
    for i, line in enumerate(lines):
        line_num = i + 1
        line = line.strip()
        if not line:
            continue
        
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as e:
            output.append(f"#P{line_num} PARSE_ERROR: {e}")
            continue
        
        obj_type = obj.get("type", "?")
        ts = obj.get("timestamp", "")
        ts_str = ts_to_gmt8(ts) if ts else ""
        
        if obj_type == "session":
            ver = obj.get("version", "?")
            sid = obj.get("id", "?")[:12]
            cwd = obj.get("cwd", "?")
            output.append(f"#P{line_num} [{ts_str} GMT+8] SESSION_INIT: version={ver}, id={sid}..., cwd={cwd}")
            continue
        
        if obj_type == "model":
            provider = obj.get("provider", "?")
            model = obj.get("modelId", "?")
            output.append(f"#P{line_num} [{ts_str} GMT+8] MODEL: provider={provider}, model={model}")
            continue
        
        if obj_type == "thinkingLevel":
            level = obj.get("thinkingLevel", "?")
            output.append(f"#P{line_num} [{ts_str} GMT+8] THINKING_LEVEL: {level}")
            continue
        
        if obj_type == "custom":
            custom_type = obj.get("customType", "?")
            data = obj.get("data", {})
            output.append(f"#P{line_num} [{ts_str} GMT+8] CUSTOM({custom_type}): {truncate(json.dumps(data, ensure_ascii=False), 300)}")
            continue
        
        if obj_type == "message":
            msg = obj.get("message", {})
            role = msg.get("role", "?")
            content = msg.get("content", "")
            tool_calls = msg.get("tool_calls", [])
            
            parts = extract_content_parts(content)
            
            header = f"#P{line_num} [{ts_str} GMT+8] MESSAGE({role}):"
            output.append(header)
            
            for ptype, ptext in parts:
                if ptype == "thinking":
                    output.append(f"    THINKING [{len(ptext)} chars]:")
                    for tline in ptext.split("\n"):
                        output.append(f"        {tline}")
                elif ptype == "text":
                    if len(ptext) > 1000:
                        output.append(f"    TEXT [{len(ptext)} chars]: {ptext[:1000]}...")
                    else:
                        output.append(f"    TEXT: {ptext}")
                elif ptype == "tool_use":
                    output.append(f"    TOOL_USE: {truncate(ptext, 600)}")
                elif ptype == "tool_result":
                    if isinstance(ptext, list):
                        for tr in ptext:
                            if isinstance(tr, dict) and tr.get("type") == "text":
                                output.append(f"    TOOL_RESULT [{len(tr.get('text',''))} chars]: {truncate(tr.get('text',''), 500)}")
                            else:
                                output.append(f"    TOOL_RESULT: {truncate(str(tr), 500)}")
                    else:
                        output.append(f"    TOOL_RESULT [{len(str(ptext))} chars]: {truncate(str(ptext), 500)}")
                else:
                    output.append(f"    [{ptype}]: {truncate(ptext, 400)}")
            
            for tc in tool_calls:
                fn = tc.get("function", {})
                name = fn.get("name", "?")
                args = fn.get("arguments", "{}")
                output.append(f"    TOOL_CALL: {name}({truncate(args, 500)})")
            
            if role == "tool":
                tcid = msg.get("tool_call_id", "")
                if tcid:
                    output.append(f"    tool_call_id: {tcid}")
            
            output.append("")
            continue
        
        output.append(f"#P{line_num} [{ts_str} GMT+8] TYPE={obj_type}: {truncate(json.dumps(obj, ensure_ascii=False), 200)}")
    
    result = "\n".join(output)
    outpath = r'd:\VeriTask\archived\parsed_timeline.txt'
    with open(outpath, 'w', encoding='utf-8') as f:
        f.write(result)
    print(f"Written to {outpath} ({len(result)} chars, {len(output)} lines)")
    print("\n--- BEGIN OUTPUT ---\n")
    print(result)

if __name__ == "__main__":
    main()
