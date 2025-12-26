#!/usr/bin/env python
"""
Copyright 2025 Bayer Crop Science. All Rights Reserved.
Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

__author__ = "Srinivas Esarapu"
__version__ = "v0.0.1"

import streamlit as st
from strands import Agent
from strands.models import BedrockModel
# from strands_tools import http_request  # Unused
from strands.tools.mcp import MCPClient
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


# Configure logging once so MCP tool errors don't spam stack traces
mcp_logger = logging.getLogger("strands.tools.mcp.mcp_client")
mcp_logger.setLevel(logging.CRITICAL)
mcp_logger.propagate = False

mcp_session_logger = logging.getLogger("mcp.shared.session")
mcp_session_logger.setLevel(logging.CRITICAL)
mcp_session_logger.propagate = False


def get_agent() -> Agent:
    """Create (or reuse) a GitHub MCP-backed Agent for Streamlit.

    The MCP client is passed as a ToolProvider to the Agent, so tools are
    loaded lazily and reused across Streamlit reruns via session_state.
    """

    if "agent" in st.session_state:
        return st.session_state.agent

    # Bayer Enterprise GitHub configuration
    github_token = os.environ.get("GITHUB_ACCESS_TOKEN")
    if not github_token:
        raise RuntimeError(
            "GITHUB_ACCESS_TOKEN is not set in the environment. "
            "Please export it before running the Streamlit app."
        )
    github_host = "github.bayer.com"

    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-github"],
        env={
            "GITHUB_PERSONAL_ACCESS_TOKEN": github_token,
            "GH_HOST": github_host,
        },
    )

    # MCPClient implements ToolProvider, so we can pass it directly as a tool
    mcp_client = MCPClient(lambda: stdio_client(server_params))

    model = BedrockModel(
        model_id="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        region_name="us-east-1",
    )

    agent = Agent(
        system_prompt=SYSTEM_PROMPT,
        tools=[mcp_client],
        model=model,
    )

    st.session_state.agent = agent
    st.session_state.mcp_client = mcp_client
    return agent


def strmlit_app():
    st.set_page_config(page_title="Bedrock Agent Chat", page_icon="💬")
    st.title("Bedrock Agent Chat")
    # Initialize agent once and keep in session state
    if "agent" not in st.session_state:
        st.session_state.agent = get_agent()

    st.write("Type your question below. Type `exit` or `quit` to stop.")

    # Chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for role, content in st.session_state.messages:
        with st.chat_message(role):
            st.markdown(content)

    user_input = st.chat_input("SRINI:")

    if user_input:
        if user_input.lower() in ["exit", "quit", "q"]:
            st.stop()

        # Show user message
        st.session_state.messages.append(("user", user_input))
        with st.chat_message("user"):
            st.markdown(user_input)

        # Call the agent
        with st.chat_message("assistant"):
            try:
                response = st.session_state.agent(user_input)
                # If Agent prints to stdout and returns None, at least avoid crash
                if response is None:
                    st.write("_Agent executed (no return value). Check logs / stdout for details._")
                else:
                    st.session_state.messages.append(("assistant", str(response)))
                    st.markdown(str(response))
            except Exception as e:
                st.error(f"Error calling agent: {e}")

# Run the Streamlit UI when this script is executed via `streamlit run`.
strmlit_app()
