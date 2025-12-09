# In-Product Agent Example

This repo contains an example in-product agent whose purpose is to show you how to build your own assistant inside your app.

The agent in this example can answer questions about subscription plans, team members, and your product docs — but these are all **dummy tools**. They only exist to demonstrate the pattern; in a real setup you’d replace them with tools that call your own APIs and data stores.

What really matters is the approach:

- a **reasoning model** (GPT-5.1) that decides what to do,
- **native tools** that talk to your product (e.g. billing, teams, settings),
- a **Kapa retrieval tool via MCP** that searches your docs and guides.

Together, this gives you an in-product agent that can use both your live product data and your documentation to help users without leaving your app.


This example uses LangChain’s `create_agent` for orchestration and an OpenAI reasoning model, but you can swap this for any agent framework including none and any reasoning model that supports tools.

## Architecture Overview

Here’s how the pieces fit together inside your product:

```
┌─────────────────────────────────────────────────────────────────┐
│                     Your SaaS Product                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                      AI Agent                             │  │
│  │                   (GPT-5.1 + Tools)                       │  │
│  │                                                           │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐   │  │
│  │  │ Subscription│  │    Team     │  │   Kapa MCP Tool  │   │  │
│  │  │    Tool     │  │   Tool      │  │ (Documentation)  │   │  │
│  │  └──────┬──────┘  └──────┬──────┘  └────────┬─────────┘   │  │
│  └─────────┼────────────────┼──────────────────┼─────────────┘  │
│            │                │                  │                │
│            ▼                ▼                  │                │
│      Your APIs        Your Database            │                │
└────────────────────────────────────────────────┼────────────────┘
                                                 │
                                                 ▼
                                   ┌─────────────────────────┐
                                   │  Kapa Hosted MCP Server │
                                   │   (your-project.mcp.    │
                                   │       kapa.ai)          │
                                   └─────────────────────────┘
```

## Prerequisites

- Docker and Docker Compose
- An OpenAI API key
- An active Kapa account with a project that has a Hosted MCP Server configured (if you don't have one yet, follow the instructions below)

## Setting Up Your Kapa MCP Server

1. In the [Kapa platform](https://app.kapa.ai), click **Integrations** > **+ Add new integration**
2. Choose **Hosted MCP Server**
3. Configure:
   - **Subdomain**: This becomes `<subdomain>.mcp.kapa.ai`
   - **Server name**: The MCP server label
   - **Authentication type**: Select **API key** for in-product agents
4. Copy your API key from the integration settings

> **Important**: API key authentication is required for in-product agents. Never expose your API key in client-side code.

## Quick Start with Docker

1. Clone this repository:

```bash
git clone https://github.com/kapa-ai/langchain-agent-example.git
cd langchain-agent-example
```

2. Create your `.env` file with your credentials:

```bash
cp env.example .env
```

Edit `.env` with your values:

```bash
OPENAI_API_KEY=sk-your-openai-api-key
KAPA_MCP_SERVER_URL=https://your-project.mcp.kapa.ai
KAPA_API_KEY=your-kapa-api-key
PRODUCT_NAME=My Awesome Product
```

3. Start a shell in the container:

```bash
docker compose run --rm agent
```

4. Inside the container, run the agent:

```bash
python main.py
```

## Alternative: Local Python Setup

If you prefer running without Docker:

1. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables:

```bash
export OPENAI_API_KEY=sk-your-openai-api-key
export KAPA_MCP_SERVER_URL=https://your-project.mcp.kapa.ai
export KAPA_API_KEY=your-kapa-api-key
export PRODUCT_NAME="My Awesome Product"  # Optional
```

4. Run the demo:

```bash
python main.py
```

This starts an interactive chat session where you can ask questions.

## Example Session

```
============================================================
  My Awesome Product Assistant
============================================================

Initializing agent...

Loaded 1 tool(s) from Kapa MCP server:
  → search_my_awesome_product_knowledge_sources

👋 Hi! I'm your My Awesome Product assistant. I can help you with:

  📊 Subscription & Billing
     Ask about your plan, seats, features, or renewal dates

  👥 Team Management
     See who's on your team, their roles, and departments

  📚 Product Questions
     How-to guides, features, troubleshooting, and best practices

------------------------------------------------------------
Type 'quit' to exit
------------------------------------------------------------

You: What plan am I on?

🧠 The user is asking about their subscription...

🔧 Calling tool: get_subscription_info
✓ Tool completed

You're on the **Pro** plan with 8/10 seats used.

You: How do I set up webhooks?

🧠 This is a product question, I should search the documentation...

🔧 Calling tool: search_my_awesome_product_knowledge_sources
   query: how to set up webhooks
✓ Tool completed

To set up webhooks, go to Settings → Integrations → Webhooks...
```

## Project Structure

```
langchain-agent-example/
├── Dockerfile              # Container image definition
├── docker-compose.yml      # Docker Compose configuration
├── env.example             # Environment variable template
├── main.py                 # Entry point with interactive demo
├── requirements.txt        # Python dependencies
└── src/
    ├── __init__.py
    ├── agent.py           # LangChain agent definition (using create_agent)
    └── tools/
        ├── __init__.py
        ├── subscription.py # Mock subscription info tool
        └── team.py        # Mock team members tool
```

## How It Works

### 1. Agent Architecture

The agent is built using LangChain's `create_agent` function, which provides a streamlined way to implement a ReAct (Reasoning + Acting) loop:

```python
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

# ... (tools and system_prompt defined)

llm = ChatOpenAI(
    model="gpt-5.1",
    reasoning={"effort": "medium", "summary": "detailed"},
    temperature=0
)

agent = create_agent(
    model=llm,
    tools=tools,
    system_prompt=system_prompt,
)
```

This setup allows the GPT-5.1 model to:
- **Reason**: Analyze the user's query and determine the best course of action (e.g., which tool to call).
- **Act**: Invoke the selected tool with appropriate arguments.
- **Respond**: Generate a final answer based on tool outputs or direct knowledge.

### 2. Kapa MCP Integration

The Kapa Hosted MCP Server is integrated as a tool using `langchain-mcp-adapters`. This allows the agent to access your product's documentation:

```python
from langchain_mcp_adapters.client import MultiServerMCPClient

mcp_client = MultiServerMCPClient({
    "kapa": {
        "transport": "streamable_http",
        "url": "https://your-project.mcp.kapa.ai",
        "headers": {
            "Authorization": f"Bearer {api_key}"
        }
    }
})

# Get tools from MCP server (e.g., search_yourproduct_knowledge_sources)
mcp_tools = await mcp_client.get_tools()
```

### 3. Custom Tools

Internal tools (like `get_subscription_info` and `get_team_members`) are defined using LangChain's `@tool` decorator. These represent interactions with your product's internal APIs or databases.

```python
from langchain_core.tools import tool

@tool
def get_subscription_info(user_id: str = None) -> str:
    """Get information about the user's subscription plan."""
    # In production: call your billing API
    return "Mock subscription data"
```

## Learn More

- [Kapa Hosted MCP Server Documentation](https://docs.kapa.ai/integrations/mcp)
- [LangChain Agents Documentation](https://docs.langchain.com/oss/python/langchain/agents)