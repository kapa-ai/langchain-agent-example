# In-Product Agent Example

This repo contains an example in-product agent whose purpose is to show you how to build your own assistant inside your app.

The agent in this example can answer questions about subscription plans, team members, and your product docs — but these are all **dummy tools**. They only exist to demonstrate the pattern; in a real setup you’d replace them with tools that call your own APIs and data stores.

What really matters is the approach:

- a **reasoning model** (GPT-5.1) that decides what to do,
- **native tools** that talk to your product (e.g. billing, teams, settings),
- the **Kapa LangChain package**, which gives the agent search over your docs and guides and lookup of whole documents.

Together, this gives you an in-product agent that can use both your live product data and your documentation to help users without leaving your app.

This example uses LangChain’s `create_agent` for orchestration and an OpenAI reasoning model, but you can swap this for any agent framework including none and any reasoning model that supports tools.

## Prerequisites

- Docker and Docker Compose
- An OpenAI API key
- An active Kapa account with a project that has knowledge sources indexed (if you don't have one yet, follow [Index your first source](https://docs.kapa.ai/getting-started/index-your-first-source))

## Connecting Your Kapa Project

1. In the [Kapa platform](https://app.kapa.ai), select your project
2. Open **API Keys** under **Deploy** and click **Add API key**, then copy the private key
3. Open **Settings** > **Projects** and click **Copy project ID** next to your project

> **Important**: The agent runs on your backend. Never expose your API key in client-side code.

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
KAPA_API_KEY=your-kapa-api-key
KAPA_PROJECT_ID=your-project-id
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
export KAPA_API_KEY=your-kapa-api-key
export KAPA_PROJECT_ID=your-project-id
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

Loaded 2 tool(s) from the Kapa LangChain package:
  → search_knowledge_sources
  → get_knowledge_documents

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

🔧 Calling tool: search_knowledge_sources
   query: how to set up webhooks
✓ Tool completed

To set up webhooks, go to Settings → Integrations → Webhooks...

Source: https://docs.example.com/webhooks#setup

You: What's my plan and who are the admins on my team?

🧠 The user is asking two things - subscription info and team members filtered by role...

🔧 Calling tool: get_subscription_info
✓ Tool completed

🧠 Now I need to get the admin team members...

🔧 Calling tool: get_team_members
   role: admin
✓ Tool completed

You're on the **Pro** plan with 8/10 seats used. Your team has 2 admins:
- Alice Smith (alice.s@acme.com) - Engineering
- Diana Ross (diana.r@acme.com) - Product
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

model = ChatOpenAI(
    model="gpt-5.1",
    reasoning={"effort": "medium", "summary": "detailed"},
)

agent = create_agent(
    model=model,
    tools=tools,
    system_prompt=system_prompt,
)
```

The agent follows a **ReAct (Reasoning + Acting) loop**:

1. **Reason** — Analyze the situation and decide what to do next
2. **Act** — Call one or more tools
3. **Observe** — See the results
4. **Repeat** — Go back to step 1 if more information is needed
5. **Respond** — Generate a final answer once satisfied

This loop is flexible: the agent might call one tool and respond immediately, or it might chain several tool calls with reasoning steps in between. It decides dynamically based on what it learns from each tool result.

### 2. Kapa Tools

The Kapa LangChain package provides the agent's knowledge tools through `KapaToolkit`. `search_knowledge_sources` returns the most relevant chunks of your documentation with their source links, and `get_knowledge_documents` fetches a whole page when a chunk is not enough:

```python
from langchain_kapa_ai import KapaToolkit

# Reads KAPA_API_KEY and KAPA_PROJECT_ID from the environment when not passed
kapa_tools = KapaToolkit().get_tools()
```

The toolkit also accepts retrieval and document settings, for example `source_group_ids` to restrict both tools to some of your sources. The [package reference](https://docs.kapa.ai/retrieval/frameworks/langchain) lists them.

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

- [Kapa LangChain package reference](https://docs.kapa.ai/retrieval/frameworks/langchain)
- [Add knowledge base search to a LangChain agent](https://docs.kapa.ai/examples/langchain-knowledge-base-search)
- [LangChain Agents Documentation](https://docs.langchain.com/oss/python/langchain/agents)