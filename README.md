# In-Product Agent with Kapa Hosted MCP Server

This is a **reference implementation** showing how to build an AI agent that lives inside your product. The kind of assistant users can chat with directly in your app—asking about their account, getting help with features, or taking actions.

The specific tools in this example (subscription info, team members) are just **placeholders**. In your own implementation, you'd replace these with tools that call your actual APIs and do whatever makes sense for your product. The pattern stays the same.

## What This Example Shows

1. **Your own tools** – Custom tools that call your product's APIs (we show mock examples for subscription and team data)
2. **Kapa MCP tool** – Answers product questions by searching your documentation via the hosted MCP server
3. **A reasoning model** – GPT-5.1 decides which tool to use based on what the user asks

```
┌─────────────────────────────────────────────────────────────────┐
│                     Your SaaS Product                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                 AI Agent (GPT-5.1)                        │  │
│  │                                                           │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐  │  │
│  │  │ Subscription│  │    Team     │  │   Kapa MCP Tool  │  │  │
│  │  │    Tool     │  │   Tool      │  │ (Documentation)  │  │  │
│  │  └──────┬──────┘  └──────┬──────┘  └────────┬─────────┘  │  │
│  │         │                │                   │            │  │
│  └─────────┼────────────────┼───────────────────┼────────────┘  │
│            │                │                   │               │
│            ▼                ▼                   │               │
│    ┌──────────────┐  ┌──────────────┐          │               │
│    │  Billing DB  │  │   Users DB   │          │               │
│    └──────────────┘  └──────────────┘          │               │
└────────────────────────────────────────────────┼───────────────┘
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
- A Kapa Hosted MCP Server with API key authentication

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

3. Start the container:

```bash
docker compose run --rm agent
```

4. Inside the container, run the agent:

```bash
python main.py
```

### Configuration

| Environment Variable | Required | Description |
|---------------------|----------|-------------|
| `OPENAI_API_KEY` | Yes | Your OpenAI API key |
| `KAPA_MCP_SERVER_URL` | Yes | Your Kapa MCP server URL (e.g., `https://your-project.mcp.kapa.ai`) |
| `KAPA_API_KEY` | Yes | API key for authenticating with your Kapa MCP server |
| `PRODUCT_NAME` | No | Your product name (shown in agent responses). Defaults to `<Your Product>` |

### Docker Commands

```bash
# Build the image
docker compose build

# Start a shell in the container
docker compose run --rm agent

# Once inside the container:
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

### Example Session

```
============================================================
  My Awesome Product Assistant
============================================================

Initializing agent...

Loaded 1 tool(s) from Kapa MCP server:
  → search_my_awesome_product_knowledge_sources

👋 Hi! I'm your My Awesome Product assistant. I can help you with:

  📊 Subscription & Billing
  👥 Team Management
  📚 Product Questions

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
    ├── agent.py           # Agent configuration (using create_agent)
    └── tools/
        ├── __init__.py
        ├── subscription.py # Subscription info tool
        └── team.py        # Team members tool
```

## How It Works

### 1. Agent Architecture

The agent uses LangChain's `create_agent` with a reasoning model:

```python
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

# Configure the model with reasoning enabled
model = ChatOpenAI(
    model="gpt-5.1",
    reasoning={"effort": "medium", "summary": "detailed"},
)

# Create the agent
agent = create_agent(
    model=model,
    tools=[get_subscription_info, get_team_members, *mcp_tools],
    system_prompt=system_prompt,
)
```

### 2. MCP Integration

The Kapa MCP server is connected using `langchain-mcp-adapters`:

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

# Get tools from MCP server
mcp_tools = await mcp_client.get_tools()
```

### 3. Custom Tools

Internal tools use LangChain's `@tool` decorator:

```python
from langchain_core.tools import tool

@tool
def get_subscription_info(user_id: str = None) -> str:
    """Get information about the user's subscription plan."""
    # In production: call your billing API
    return subscription_data
```

## Customizing for Your Product

### Replace Mock Data

The example uses mock data for subscription and team information. In production:

1. **`src/tools/subscription.py`**: Connect to your billing system (Stripe, etc.)
2. **`src/tools/team.py`**: Connect to your user management database

### Add More Tools

You can add any tools your in-product agent needs:

```python
@tool
def create_project(name: str, template: str = "default") -> str:
    """Create a new project for the user."""
    # Your implementation
    pass

@tool  
def get_recent_activity(days: int = 7) -> str:
    """Get the user's recent activity in the product."""
    # Your implementation
    pass
```

### Customize the System Prompt

Edit `SYSTEM_PROMPT_TEMPLATE` in `src/agent.py` to match your product's personality and capabilities.

## Best Practices

1. **Keep API keys server-side**: Never expose your Kapa API key in client-side code
2. **Add authentication context**: In production, pass user context to tools for proper authorization
3. **Rate limiting**: Kapa enforces 60 requests/minute per API key by default
4. **Error handling**: The MCP tools handle errors gracefully, but consider adding retry logic for production

## Learn More

- [Kapa Hosted MCP Server Documentation](https://docs.kapa.ai/integrations/mcp)
- [LangChain Agents](https://docs.langchain.com/oss/python/langchain/agents)
- [LangChain MCP Adapters](https://github.com/langchain-ai/langchain-mcp-adapters)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)

## Support

For questions about:
- **This example**: Open an issue on this repository
- **Kapa MCP Server**: Contact support@kapa.ai
- **LangChain/LangGraph**: Visit the [LangChain Discord](https://discord.gg/langchain)

