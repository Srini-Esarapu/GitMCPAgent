## GitMCPAgent

This repository contains two ways to run a GitHub MCP (Model Context Protocol) agent against Bayer Enterprise GitHub (`github.bayer.com`):

- A **terminal-based agent**: `GitMcpAgent.py`
- A **Streamlit web UI**: `GitMcpAgent_Streamlit.py`

Both use the same GitHub MCP server (`@modelcontextprotocol/server-github`) and an AWS Bedrock Claude model.

---

## 1. Prerequisites

- Python 3.10+ installed
- Node.js and `npx` installed (for `@modelcontextprotocol/server-github`)
- A valid GitHub Personal Access Token for Bayer Enterprise GitHub with appropriate read permissions
- AWS credentials configured for Bedrock (so `BedrockModel` can call Claude)

### Python packages

Install required Python dependencies (from the project root):

```bash
pip install streamlit strands strands-tools mcp
```

If you use a virtual environment, activate it before installing:

```bash
python -m venv .venv
source .venv/bin/activate
pip install streamlit strands strands-tools mcp
```

### Environment variables

Both entrypoints require a GitHub token via an environment variable:

- Terminal app (`GitMcpAgent.py`): uses `GITHUB_ACCESS_TOKEN`
- Streamlit app (`GitMcpAgent_Streamlit.py`): uses `GITHUB_PERSONAL_ACCESS_TOKEN`

Set them in the shell **before** running either script (replace `...` with your real token):

```bash
export GITHUB_ACCESS_TOKEN=ghp_your_token_here
export GITHUB_PERSONAL_ACCESS_TOKEN=ghp_your_token_here
```

To make this persistent, add the above `export` lines to `~/.zshrc` and then run:

```bash
source ~/.zshrc
```

---

## 2. Running the terminal-based agent (`GitMcpAgent.py`)

This script runs an interactive MCP agent in your terminal.

From the project root:

```bash
export GITHUB_ACCESS_TOKEN=ghp_your_token_here   # if not already set
python GitMcpAgent.py
```

You’ll see prompts like:

- The script connects to `github.bayer.com` via the MCP server
- It lists how many MCP tools were loaded
- It then asks you to type your question

Usage:

- Type your question about Bayer Enterprise GitHub and press Enter
- Type `exit`, `quit`, or `q` to stop the agent

---

## 3. Running the Streamlit web UI (`GitMcpAgent_Streamlit.py`)

This script exposes the same kind of MCP-backed agent via a Streamlit chat interface.

From the project root:

```bash
export GITHUB_PERSONAL_ACCESS_TOKEN=ghp_your_token_here   # if not already set
streamlit run GitMcpAgent_Streamlit.py
```

Then open the URL printed by Streamlit (usually `http://localhost:8501`).

In the UI:

- The page title is **"Bedrock Agent Chat"**
- Type your question in the chat input labelled `SRINI:`
- Type `exit`, `quit`, or `q` to stop the app within that session

The app uses MCP tools from the GitHub Enterprise MCP server in **read-only** mode and an AWS Bedrock Claude model to answer questions.

---

## 4. Notes and troubleshooting

- If you see an error like `GITHUB_ACCESS_TOKEN is not set` or `GITHUB_PERSONAL_ACCESS_TOKEN is not set`, make sure you exported the correct environment variable in the same terminal before running the script.
- If the MCP server fails to start, ensure `node` and `npx` are installed and on your PATH:
	```bash
	node -v
	npx -v
	```
- If Bedrock calls fail, verify that your AWS credentials and region are configured correctly (for example via `aws configure`).
- All MCP tools are used in **read-only** mode; the agent will refuse any request to write, modify, or delete GitHub content.
