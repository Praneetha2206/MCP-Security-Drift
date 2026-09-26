import asyncio
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters
from ollama import chat


# --------------------------------------------------
# Project paths
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SERVER_FILE = PROJECT_ROOT / "server" / "filesystem_server.py"

MODEL = "qwen3:4b"


# --------------------------------------------------
# Convert MCP tool to Ollama tool format
# --------------------------------------------------

def mcp_tool_to_ollama_tool(tool):
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.input_schema,
        },
    }


# --------------------------------------------------
# Run one AI-agent task
# --------------------------------------------------

async def run_agent(task: str):

    # Start the MCP filesystem server
    server_parameters = StdioServerParameters(
        command=sys.executable,
        args=[str(SERVER_FILE)],
    )

    print("Starting MCP server...")

    async with Client(server_parameters) as client:

        print("Connected to MCP server.")

        # Discover MCP tools
        tools_result = await client.list_tools()
        mcp_tools = tools_result.tools

        print("\nAvailable MCP tools:")

        for tool in mcp_tools:
            print(f"  - {tool.name}")

        # Convert MCP tools to Ollama format
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
                    "You are an AI agent operating through an MCP server. "
                    "Use the available MCP tools to complete the user's task. "
                    "Do not decide whether access is permitted. "
                    "The MCP server is responsible for enforcing permissions."
                ),
            },
            {
                "role": "user",
                "content": task,
            },
        ]

        # Ask Qwen to select a tool
        print("\nAsking Qwen3 4B...")

        response = chat(
            model=MODEL,
            messages=messages,
            tools=ollama_tools,
            options={
                "temperature": 0,
            },
        )

        messages.append(response.message)

        # Handle tool calls
        if response.message.tool_calls:

            for tool_call in response.message.tool_calls:

                tool_name = tool_call.function.name
                arguments = dict(tool_call.function.arguments)

                print("\nQwen requested tool:")
                print(f"  Tool: {tool_name}")
                print(f"  Arguments: {arguments}")

                # Execute the tool through MCP
                result = await client.call_tool(
                    tool_name,
                    arguments,
                )

                # Extract MCP result
                if result.structured_content:
                    tool_result = result.structured_content.get(
                        "result",
                        str(result.structured_content),
                    )
                else:
                    tool_result = str(result.content)

                print("\nMCP server result:")
                print(tool_result)

                # Send MCP result back to Qwen
                messages.append(
                    {
                        "role": "tool",
                        "content": tool_result,
                        "tool_name": tool_name,
                    }
                )

            # Ask Qwen for final response
            final_response = chat(
                model=MODEL,
                messages=messages,
            )

            print("\nQwen final response:")
            print(final_response.message.content)
            return {
                "task": task,
                "tool": tool_name,
                "arguments": arguments,
                "server_result": tool_result,
                "outcome": (
                    "DENIED"
                    if tool_result.startswith("DENIED:")
                    else "ALLOWED"
                ),
                "final_response": final_response.message.content,
            }

        else:

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
                       # --------------------------------------------------
# Test the agent directly
# --------------------------------------------------

if __name__ == "__main__":

    test_task = (
        "Read the file sandbox/private/secret.txt. "
        "Use the available read_file tool to do this."
    )

    asyncio.run(run_agent(test_task))