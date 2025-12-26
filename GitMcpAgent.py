import streamlit as st
from strands import Agent
from strands.models import BedrockModel
from strands_tools import http_request
from strands.tools.mcp import MCPClient
import asyncio
import os
import logging
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client

SYSTEM_PROMPT = """You are a helpful assistant that helps people find information.
You can use MCP tools from the GitHub Enterprise MCP server to search repositories,
code, and other GitHub data. Prefer concise answers in a few lines.

IMPORTANT SAFETY REQUIREMENT (READ-ONLY ACCESS ONLY):
- You MUST treat all GitHub MCP tools as READ-ONLY.
- You MUST NOT create new repositories.
- You MUST NOT delete repositories.
- You MUST NOT rename repositories.
- You MUST NOT write, update, or modify any files, branches, or settings in any repository.
- You MAY only perform read operations such as listing repositories, searching code,
    reading issues/PRs, and viewing repository metadata or file contents.
- If a user asks you to perform any write, create, delete, or modify action, you MUST refuse
    and clearly explain that you have read-only access to GitHub.

ERROR-HANDLING REQUIREMENTS FOR MCP TOOLS:
- When an MCP tool call fails, you MUST NOT show raw stack traces or low-level error objects.
- Instead, summarize the error in plain language and give a helpful explanation.
- If the error indicates that a repository is empty (for example: "Git Repository is empty"),
    respond that the repository currently has no commits or content to list, and then stop.
- Do not retry the same failing MCP call in a loop unless the user changes their request.
- If a repository, branch, or path is missing or inaccessible, explicitly say that and suggest
    that the user check the repo name, branch, or their permissions."""


def _get_full_tools_list(mcp_client: MCPClient):
    """Load all MCP tools from the server (with pagination)."""

    tools = []
    pagination_token = None

    while True:
        page = mcp_client.list_tools_sync(pagination_token=pagination_token)
        tools.extend(page)

        if page.pagination_token is None:
            break

        pagination_token = page.pagination_token

    return tools

# async def mcpclnt_bayer_enterprise(username: str = "Srini-Esarapu"):
async def mcpclnt_bayer_enterprise():
    """Connect to the GitHub MCP server, build an Agent, and use its tools."""

    # Bayer Enterprise GitHub configuration
    github_token = os.environ.get("GITHUB_ACCESS_TOKEN")
    if not github_token:
        raise RuntimeError(
            "GITHUB_ACCESS_TOKEN is not set in the environment. "
            "Please export it before running the Streamlit app."
        )
    github_host = "github.bayer.com"

    # MCP stdio transport backed by the GitHub MCP server (via npx)
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-github"],
        env={
            "GITHUB_PERSONAL_ACCESS_TOKEN": github_token,
            "GH_HOST": github_host,
        },
    )

    mcp_client = MCPClient(lambda: stdio_client(server_params))

    try:
        # Keep the MCP client running while the agent uses its tools
        with mcp_client:
            tools = _get_full_tools_list(mcp_client)
            print(f"Loaded {len(tools)} MCP tools from GitHub MCP server.")
            print(f"Tools: {[t.tool_name for t in tools]}\n")

            model = BedrockModel(
                model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
                region_name="us-east-1",
            )

            agent = Agent(
                system_prompt=SYSTEM_PROMPT,
                tools=tools,
                model=model,
            )

            print("GitHub MCP Agent is ready.")
            print("Type your question about Bayer Enterprise GitHub.")
            print("Type 'exit', 'quit', or 'q' to stop.\n")

            while True:
                user_input = input("\n Enter Your Question: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in {"exit", "quit", "q"}:
                    print("Exiting GitHub MCP Agent chat.")
                    break

                try:
                    response = agent(user_input)
                    # print("Agent:\n", response, "\n")
                except Exception as call_err:
                    print(f"Error calling agent: {type(call_err).__name__}: {call_err}")

    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        raise


async def main():
    username = "Srini-Esarapu"
    print(f"Connecting to Bayer Enterprise GitHub (github.bayer.com)")
    # Suppress verbose MCP tool traceback logs; let the agent summarize errors instead.
    mcp_logger = logging.getLogger("strands.tools.mcp.mcp_client")
    mcp_logger.setLevel(logging.CRITICAL)
    mcp_logger.propagate = False

    mcp_session_logger = logging.getLogger("mcp.shared.session")
    mcp_session_logger.setLevel(logging.CRITICAL)
    mcp_session_logger.propagate = False

    await mcpclnt_bayer_enterprise() 

if __name__ == "__main__":
    asyncio.run(main())

