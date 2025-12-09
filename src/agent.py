"""
In-Product Agent with Kapa MCP Server Integration

This module implements a LangChain agent using create_agent that can:
1. Answer questions about the user's subscription
2. Provide information about team members
3. Answer product questions using Kapa's MCP server

The agent is designed to live inside a fictional SaaS product's web app,
helping users with both operational tasks and product knowledge questions.
"""

import os

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient

from src.tools import get_subscription_info, get_team_members


# ANSI escape codes for terminal styling
class Style:
    ITALIC = "\033[3m"
    DIM = "\033[2m"
    RESET = "\033[0m"


# System prompt template for the agent
# Note: LangChain automatically injects tool schemas (names, descriptions, arguments) into the
# model's context. The system prompt should focus on WHEN/HOW to use tools, not describe what
# they do - that's handled by the @tool decorator descriptions.
SYSTEM_PROMPT_TEMPLATE = """You are an intelligent assistant embedded in {product_name}.

You have access to three types of tools:

- `get_subscription_info`: Use this when users ask about their plan, billing, pricing, seat limits, 
  renewal dates, or what features are included in their subscription.

- `get_team_members`: Use this when users ask about who is on their team, team member roles, 
  permissions, departments, or recent activity. You can filter by role or department if needed.

- `search_{product_name}_knowledge_sources`: Use this for ANY questions about how to use 
  {product_name} - features, configuration, best practices, troubleshooting, or "how do I...?" 
  questions. This searches the official {product_name} documentation and returns accurate, 
  up-to-date information. ALWAYS prefer this tool over guessing when users ask product questions.

## Guidelines

- Be helpful, concise, and professional
- For product/feature questions, ALWAYS use the knowledge search tool first to get accurate answers
- For account questions (subscription, team), use the appropriate internal tools
- If you're unsure about something, say so rather than guessing
- Format responses clearly using markdown when appropriate

You're an assistant within the product - users expect you to know about their account and 
be knowledgeable about {product_name} itself."""


async def create_in_product_agent(
    mcp_server_url: str | None = None,
    mcp_api_key: str | None = None,
    product_name: str | None = None,
    model_name: str = "gpt-5.1",
):
    """
    Create the in-product agent with all tools configured.
    
    Args:
        mcp_server_url: URL of the Kapa MCP server (e.g., https://your-project.mcp.kapa.ai)
        mcp_api_key: API key for authenticating with the Kapa MCP server
        product_name: Name of your product (shown in agent responses)
        model_name: OpenAI model to use for the agent
    
    Returns:
        A LangChain agent ready to handle user queries.
    """
    # Get configuration from environment if not provided
    mcp_server_url = mcp_server_url or os.getenv("KAPA_MCP_SERVER_URL")
    mcp_api_key = mcp_api_key or os.getenv("KAPA_API_KEY")
    product_name = product_name or os.getenv("PRODUCT_NAME", "<Your Product>")
    
    if not mcp_server_url:
        raise ValueError(
            "KAPA_MCP_SERVER_URL must be set either as argument or environment variable. "
            "This should be your Kapa MCP server URL (e.g., https://your-project.mcp.kapa.ai)"
        )
    
    if not mcp_api_key:
        raise ValueError(
            "KAPA_API_KEY must be set either as argument or environment variable. "
            "This is your Kapa API key for the MCP server."
        )
    
    # Collect all tools
    # Start with our custom internal tools
    tools = [get_subscription_info, get_team_members]
    
    # Add Kapa MCP tools for product knowledge
    # Using streamable HTTP transport with API key authentication
    mcp_client = MultiServerMCPClient(
        {
            "kapa": {
                "transport": "streamable_http",
                "url": mcp_server_url,
                "headers": {
                    "Authorization": f"Bearer {mcp_api_key}"
                }
            }
        }
    )
    
    # Get tools from the MCP server
    mcp_tools = await mcp_client.get_tools()
    tools.extend(mcp_tools)
    
    print(f"Loaded {len(mcp_tools)} tool(s) from Kapa MCP server:")
    for tool in mcp_tools:
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
