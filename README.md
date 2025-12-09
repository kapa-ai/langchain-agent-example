# In-Product Agent with Kapa Hosted MCP Server

This example demonstrates how to build an **in-product AI agent** using LangGraph and the **Kapa Hosted MCP Server**. The agent is designed to live inside a SaaS product's web app, helping users with both operational tasks and product knowledge questions.

## What This Example Shows

This agent combines:

1. **Internal Tools** - Custom tools that interact with your product's data (subscription info, team members)
2. **Kapa MCP Server** - A hosted MCP server that provides semantic search over your product documentation

```
┌─────────────────────────────────────────────────────────────────┐
│                     Your SaaS Product                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    LangGraph Agent                        │  │
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

This will:
1. Initialize the agent with all tools
2. Run a few example queries to demonstrate capabilities
3. Start an interactive chat session

### Example Interactions

```
🧑 User: What subscription plan am I on?

🤖 Assistant: You're on the **Pro** plan with the following details:
- **Status**: Active
- **Seats**: 8/10 used (2 available)
- **Billing**: Annual at $49.99/month
...

🧑 User: Who are the admins on my team?

🤖 Assistant: Your team has 2 admins:
- **Sarah Chen** (sarah.chen@acme.com) - Engineering
- **Marcus Johnson** (marcus.j@acme.com) - Product
...

🧑 User: How do I set up a webhook integration?

🤖 Assistant: [Uses Kapa MCP to search your documentation and provide accurate instructions]
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
    ├── agent.py           # LangGraph agent definition
    └── tools/
        ├── __init__.py
        ├── subscription.py # Subscription info tool
        └── team.py        # Team members tool
```

## How It Works

### 1. Agent Architecture

The agent uses LangGraph's `StateGraph` with a simple but powerful pattern:

```python
# Define state
class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

# Build graph
graph_builder = StateGraph(AgentState)
graph_builder.add_node("agent", agent_node)
graph_builder.add_node("tools", ToolNode(tools))

# Agent decides: respond or use tools
graph_builder.add_conditional_edges("agent", tools_condition)
graph_builder.add_edge("tools", "agent")  # Loop back after tool use
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

Edit `SYSTEM_PROMPT` in `src/agent.py` to match your product's personality and capabilities.

## Best Practices

1. **Keep API keys server-side**: Never expose your Kapa API key in client-side code
2. **Add authentication context**: In production, pass user context to tools for proper authorization
3. **Rate limiting**: Kapa enforces 60 requests/minute per API key by default
4. **Error handling**: The MCP tools handle errors gracefully, but consider adding retry logic for production

## Learn More

- [Kapa Hosted MCP Server Documentation](https://docs.kapa.ai/integrations/mcp)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangChain MCP Adapters](https://github.com/langchain-ai/langchain-mcp-adapters)
- [Model Context Protocol Specification](https://modelcontextprotocol.io/)

## Support

For questions about:
- **This example**: Open an issue on this repository
- **Kapa MCP Server**: Contact support@kapa.ai
- **LangChain/LangGraph**: Visit the [LangChain Discord](https://discord.gg/langchain)

