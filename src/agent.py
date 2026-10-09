"""
In-Product Agent with the Kapa LangChain package

This module implements a LangChain agent using create_agent that can:
1. Answer questions about the user's subscription
2. Provide information about team members
3. Answer product questions by searching the Kapa knowledge base and reading
   whole documents from it

The agent is designed to live inside a fictional SaaS product's web app,
helping users with both operational tasks and product knowledge questions.
"""

import os

from langchain.agents import create_agent
from langchain_kapa_ai import KapaToolkit
from langchain_openai import ChatOpenAI

from src.tools import get_subscription_info, get_team_members


# ANSI escape codes for terminal styling
class Style:
    ITALIC = "\033[3m"
    DIM = "\033[2m"
    RESET = "\033[0m"


# System prompt template for the agent
# Note: LangChain automatically injects tool schemas (names, descriptions, arguments) into the
# model's context. The system prompt should focus on WHEN/HOW to use tools, not describe what
# they do - that's handled by the tool descriptions.
SYSTEM_PROMPT_TEMPLATE = """You are an intelligent assistant embedded in {product_name}.

You have access to four tools:

- `get_subscription_info`: Use this when users ask about their plan, billing, pricing, seat limits,
  renewal dates, or what features are included in their subscription.

- `get_team_members`: Use this when users ask about who is on their team, team member roles,
  permissions, departments, or recent activity. You can filter by role or department if needed.

- `search_knowledge_sources`: Use this for ANY questions about how to use {product_name} - features,
  configuration, best practices, troubleshooting, or "how do I...?" questions. This searches the
  official {product_name} documentation and returns relevant chunks with their source links.
  ALWAYS prefer this tool over guessing when users ask product questions.

- `get_knowledge_documents`: Use this when a search chunk is not enough and you need the whole page it came
  from. Pass the chunk's source link exactly as search returned it.

## Guidelines

- Be helpful, concise, and professional
- For product/feature questions, ALWAYS use the knowledge search tool first to get accurate answers
- Cite the source links of the chunks you used, exactly as search returned them
- For account questions (subscription, team), use the appropriate internal tools
- If the documentation does not answer the question, say so rather than guessing
- Format responses clearly using markdown when appropriate

You're an assistant within the product - users expect you to know about their account and
be knowledgeable about {product_name} itself."""


def create_in_product_agent(
    kapa_api_key: str | None = None,
    kapa_project_id: str | None = None,
    product_name: str | None = None,
    model_name: str = "gpt-5.1",
):
    """
    Create the in-product agent with all tools configured.

    Args:
        kapa_api_key: API key of your Kapa project
        kapa_project_id: ID of your Kapa project
        product_name: Name of your product (shown in agent responses)
        model_name: OpenAI model to use for the agent

    Returns:
        A LangChain agent ready to handle user queries.
    """
    # Get configuration from environment if not provided
    kapa_api_key = kapa_api_key or os.getenv("KAPA_API_KEY")
    kapa_project_id = kapa_project_id or os.getenv("KAPA_PROJECT_ID")
    product_name = product_name or os.getenv("PRODUCT_NAME", "<Your Product>")

    if not kapa_api_key:
        raise ValueError(
            "KAPA_API_KEY must be set either as argument or environment variable. "
            "Create one under Deploy > API Keys in the Kapa platform."
        )

    if not kapa_project_id:
        raise ValueError(
            "KAPA_PROJECT_ID must be set either as argument or environment variable. "
            "Copy it from Settings > Projects in the Kapa platform."
        )

    # Collect all tools
    # Start with our custom internal tools
    tools = [get_subscription_info, get_team_members]

    # Add the Kapa tools for product knowledge: search returns relevant chunks with
    # their source links, and document lookup fetches a whole page when needed
    kapa_tools = KapaToolkit(api_key=kapa_api_key, project_id=kapa_project_id).get_tools()
    tools.extend(kapa_tools)

    print(f"Loaded {len(kapa_tools)} tool(s) from the Kapa LangChain package:")
    for tool in kapa_tools:
        print(f"  → {tool.name}")
    print()

    # Build the system prompt with the product name
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(product_name=product_name)

    # Configure the model with reasoning enabled
    # This allows us to see the model's thinking process
    model = ChatOpenAI(
        model=model_name,
        reasoning={
            "effort": "medium",  # 'low', 'medium', or 'high'
            "summary": "detailed",  # Show detailed reasoning summary
        },
    )

    # Create the agent using LangChain's create_agent
    # This handles the ReAct loop automatically
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=system_prompt,
    )

    return agent


async def run_agent(agent, user_message: str, verbose: bool = True):
    """
    Run the agent with a user message, streaming output to show reasoning.

    Args:
        agent: The LangChain agent
        user_message: The user's input message
        verbose: Whether to print tool calls and reasoning (default: True)

    Returns:
        The agent's response as a string
    """
    final_response = ""
    in_reasoning = False

    # Stream the agent execution to show what's happening
    async for event in agent.astream_events(
        {"messages": [{"role": "user", "content": user_message}]},
        version="v2"
    ):
        kind = event["event"]

        # Show when the LLM starts generating
        if kind == "on_chat_model_stream":
            chunk = event["data"]["chunk"]

            # Check for reasoning blocks in content_blocks
            if hasattr(chunk, "content_blocks") and chunk.content_blocks:
                for block in chunk.content_blocks:
                    if block.get("type") == "reasoning" and verbose:
                        if not in_reasoning:
                            print(f"\n🧠 {Style.DIM}{Style.ITALIC}", end="", flush=True)
                            in_reasoning = True
                        reasoning_text = block.get("reasoning", "")
                        if reasoning_text:
                            # Stream reasoning tokens inline in italic
                            print(reasoning_text, end="", flush=True)
                    elif block.get("type") == "text":
                        text = block.get("text", "")
                        if text:
                            if in_reasoning:
                                print(f"{Style.RESET}\n\n", flush=True)
                                in_reasoning = False
                            print(text, end="", flush=True)
                            final_response += text
            # Fallback to regular content streaming
            elif chunk.content:
                if in_reasoning:
                    print(f"{Style.RESET}\n\n", flush=True)
                    in_reasoning = False
                print(chunk.content, end="", flush=True)
                final_response += chunk.content

        # Show tool calls
        elif kind == "on_tool_start" and verbose:
            if in_reasoning:
                print(f"{Style.RESET}\n", flush=True)
                in_reasoning = False
            tool_name = event["name"]
            tool_input = event["data"].get("input", {})
            print(f"\n🔧 Calling tool: {tool_name}")
            if isinstance(tool_input, dict) and tool_input:
                for key, value in tool_input.items():
                    # Truncate long values
                    display_value = str(value)[:100] + "..." if len(str(value)) > 100 else value
                    print(f"   {key}: {display_value}")
            print()

        # Show when tool completes
        elif kind == "on_tool_end" and verbose:
            print(f"✓ Tool completed\n")

    # Ensure we end with a newline
    if final_response and not final_response.endswith("\n"):
        print()

    return final_response
