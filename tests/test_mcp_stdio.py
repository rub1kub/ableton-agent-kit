import os
import sys

import pytest


def test_real_stdio_handshake_and_echo(tmp_path):
    pytest.importorskip("mcp")
    import anyio
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async def exercise():
        params = StdioServerParameters(command=sys.executable, args=["-m", "ableton_agent.mcp_server"],
                                       env={**os.environ, "ABLETON_AGENT_ROOTS": str(tmp_path), "ABLETON_AGENT_WRITE": "0"})
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as client:
                await client.initialize()
                listed = await client.list_tools()
                assert len(listed.tools) == 7
                result = await client.call_tool("plan_word_echo", {"word_end_s": 1.0, "word_duration_s": 0.2,
                    "next_phrase_s": 2.0, "bpm": 120.0})
                assert not result.isError and "answers" in result.content[0].text
                blocked = await client.call_tool("live_apply_parameters", {"edits": [], "journal_directory": str(tmp_path)})
                assert blocked.isError
    anyio.run(exercise)
