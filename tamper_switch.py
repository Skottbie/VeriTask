#!/usr/bin/env python3
"""
Tamper Switch — 本机控制脚本，打开/关闭 Worker 的篡改模式。

用法:
    python tamper_switch.py on zk       # 开启 zk 篡改
    python tamper_switch.py on tee      # 开启 tee 篡改
    python tamper_switch.py on both     # 开启双重篡改
    python tamper_switch.py off         # 关闭篡改
    python tamper_switch.py status      # 查询当前状态
"""

import sys
import requests

WORKER_URL = "https://2d29518d31fd53641b70a1754c79dce1450188b2-8001.dstack-pha-prod9.phala.network"


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1].lower()

    if cmd == "status":
        r = requests.get(f"{WORKER_URL}/get_tamper_mode", timeout=10)
        r.raise_for_status()
        mode = r.json()["tamper_mode"]
        print(f"当前篡改模式: {mode}")

    elif cmd == "off":
        r = requests.post(f"{WORKER_URL}/set_tamper_mode", params={"mode": "off"}, timeout=10)
        r.raise_for_status()
        print(f"✅ 篡改已关闭: {r.json()}")

    elif cmd == "on":
        if len(sys.argv) < 3 or sys.argv[2].lower() not in ("zk", "tee", "both"):
            print("用法: python tamper_switch.py on <zk|tee|both>")
            sys.exit(1)
        mode = sys.argv[2].lower()
        r = requests.post(f"{WORKER_URL}/set_tamper_mode", params={"mode": mode}, timeout=10)
        r.raise_for_status()
        print(f"⚠️  篡改已开启 [{mode}]: {r.json()}")

    else:
        print(f"未知命令: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
