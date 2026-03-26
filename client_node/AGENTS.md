# AGENTS.md — VeriTask Client Agent

> See parent `../AGENTS.md` for full skill routing rules.
> This file adds Veriverse gateway integration for the Telegram channel.

---

## /veri 命令 — 返回 Veriverse 主菜单

当用户输入 `/veri` 时，调用 `gateway` 工具移除 peer binding，将用户路由回 veriverse-router：

1. 调用 `gateway` 工具：
```json
{
  "action": "config.patch",
  "raw": "{ bindings: [ { agentId: \"veriverse-router\", match: { channel: \"telegram\" } } ] }",
  "note": "已返回 Veriverse 主菜单 🌐 发送任意消息查看菜单"
}
```
2. gateway 自动重启后，用户将回到 veriverse-router 主菜单。
