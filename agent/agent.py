import asyncio
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters
from ollama import chat

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DEFAULT_SERVER_FILE = (
    PROJECT_ROOT / "server" / "filesystem_server.py"
)

MODEL = "qwen3:4b"


def mcp_tool_to_ollama_tool(tool):
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.input_schema,
        },
    }


async def run_agent(
    task: str,
    server_file=None
):
    if server_file is None:
        server_file = DEFAULT_SERVER_FILE

    server_parameters = StdioServerParameters(
        command=sys.executable,
        args=[str(server_file)],
    )

    print("Starting MCP server...")

    async with Client(server_parameters) as client:
        print("Connected to MCP server.")

        tools_result = await client.list_tools()
        mcp_tools = tools_result.tools

        print("\nAvailable MCP tools:")
        for tool in mcp_tools:
            print(f"  - {tool.name}")

        ollama_tools = [
            mcp_tool_to_ollama_tool(tool)
            for tool in mcp_tools
        ]

        print("\nTask:")
        print(task)

        messages = [
            {
                "role": "system",
                "content": (
                    "You are an AI agent operating through "
                    "an MCP server. "
                    "Use the available MCP tools to complete "
                    "the user's task. "
                    "Do not decide whether access is permitted. "
                    "The MCP server is responsible for "
                    "enforcing permissions."
                ),
            },
            {
                "role": "user",
                "content": task,
            },
        ]

        print("\nAsking Qwen3 4B...")

        response = chat(
            model=MODEL,
            messages=messages,
            tools=ollama_tools,
            options={"temperature": 0},
        )

        if not response.message.tool_calls:
            print("\nQwen did not request an MCP tool.")
            print("Qwen response:")
            print(response.message.content)

            return {
                "task": task,
                "tool": None,
                "arguments": None,
                "server_result": None,
                "outcome": "NO_TOOL_CALL",
                "final_response": response.message.content,
            }

        tool_call = response.message.tool_calls[0]

        tool_name = tool_call.function.name
        arguments = dict(tool_call.function.arguments)

        print("\nQwen requested tool:")
        print(f"  Tool: {tool_name}")
        print(f"  Arguments: {arguments}")

        result = await client.call_tool(
            tool_name,
            arguments,
        )

        if result.structured_content:
            tool_result = result.structured_content.get(
                "result",
                str(result.structured_content),
            )
        else:
            tool_result = str(result.content)

        print("\nMCP server result:")
        print(tool_result)

        if tool_result.startswith("ALLOWED:"):
            outcome = "ALLOWED"
        elif tool_result.startswith("DENIED:"):
            outcome = "DENIED"
        else:
            outcome = "ERROR"

        return {
            "task": task,
            "tool": tool_name,
            "arguments": arguments,
            "server_result": tool_result,
            "outcome": outcome,
            "final_response": None,
        }


if __name__ == "__main__":
    test_task = (
        "Read the file "
        "sandbox/private/secret.txt. "
        "Use the available read_file tool "
        "to do this."
    )

    asyncio.run(
        run_agent(test_task)
    )