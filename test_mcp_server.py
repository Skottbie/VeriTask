#!/usr/bin/env python3
"""Smoke test for the VeriTask MCP stdio export.

This test only verifies MCP server initialization and discoverability so it can
run even when the downstream Worker service is offline.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT_DIR = Path(__file__).resolve().parent
SERVER_PATH = ROOT_DIR / "client_node" / "veritask_mcp_server.py"
EXPECTED_TOOLS = {
    "submit_defi_tvl_task",
    "get_task_status",
    "get_task_result",
    "vt_request_task",
    "vt_get_task_status",
    "vt_get_task_result",
    "vt_verify_result",
    "vt_settle_payment",
    "vt_get_settlement_receipt",
}
EXPECTED_RESOURCES = {
    "veritask://tasks/{handle_id}",
    "veritask://results/{handle_id}",
    "veritask://receipts/{handle_id}",
}


async def main() -> None:
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_PATH)],
        cwd=str(ROOT_DIR),
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            tools_result = await session.list_tools()
            resource_templates_result = await session.list_resource_templates()

            tool_names = {tool.name for tool in tools_result.tools}
            resource_uris = {
                resource_template.uriTemplate
                for resource_template in resource_templates_result.resourceTemplates
            }

            missing_tools = EXPECTED_TOOLS - tool_names
            missing_resources = EXPECTED_RESOURCES - resource_uris

            print("Discovered tools:")
            for name in sorted(tool_names):
                print(f"- {name}")

            print("Discovered resource templates:")
            for uri in sorted(resource_uris):
                print(f"- {uri}")

            if missing_tools:
                raise SystemExit(f"Missing expected tools: {sorted(missing_tools)}")

            if missing_resources:
                raise SystemExit(
                    f"Missing expected resource templates: {sorted(missing_resources)}"
                )

            print("MCP smoke test passed.")


if __name__ == "__main__":
    asyncio.run(main())