"""
In-Product Agent with Kapa MCP Server Integration

This module implements a LangGraph-based agent that can:
1. Answer questions about the user's subscription
2. Provide information about team members
3. Answer product questions using Kapa's MCP server

The agent is designed to live inside a fictional SaaS product's web app,
helping users with both operational tasks and product knowledge questions.
"""

import os
from typing import Annotated, TypedDict

from langchain_core.messages import AnyMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_mcp_adapters.client import MultiServerMCPClient

from src.tools import get_subscription_info, get_team_members


# Agent state definition
class AgentState(TypedDict):
    """State for the in-product agent."""
    messages: Annotated[list[AnyMessage], add_messages]


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


async def create_agent(
    mcp_server_url: str | None = None,
    mcp_api_key: str | None = None,
    product_name: str | None = None,
    model_name: str = "gpt-4o-mini",
):
    """
    Create the in-product agent with all tools configured.
    
    Args:
        mcp_server_url: URL of the Kapa MCP server (e.g., https://your-project.mcp.kapa.ai)
        mcp_api_key: API key for authenticating with the Kapa MCP server
        product_name: Name of your product (shown in agent responses)
        model_name: OpenAI model to use for the agent
    
    Returns:
        A compiled LangGraph agent ready to handle user queries.
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
    
    # Initialize the LLM
    llm = ChatOpenAI(model=model_name, temperature=0)
    
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
    
    # Bind tools to the LLM
    llm_with_tools = llm.bind_tools(tools)
    
    # Build the system prompt with the product name
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(product_name=product_name)
    
    # Define the agent node
    def agent_node(state: AgentState) -> AgentState:
        """Process messages and decide whether to use tools or respond."""
        messages = state["messages"]
        
        # Add system prompt if this is the first message
        if not any(isinstance(m, SystemMessage) for m in messages):
            messages = [SystemMessage(content=system_prompt)] + messages
        
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}
    
    # Build the graph
    graph_builder = StateGraph(AgentState)
    
    # Add nodes
    graph_builder.add_node("agent", agent_node)
    graph_builder.add_node("tools", ToolNode(tools))
    
    # Add edges
    graph_builder.add_edge(START, "agent")
    graph_builder.add_conditional_edges(
        "agent",
        tools_condition,  # Routes to "tools" if tool calls present, else END
    )
    graph_builder.add_edge("tools", "agent")  # After tools, go back to agent
    
    # Compile and return
    return graph_builder.compile()


async def run_agent(agent, user_message: str, conversation_history: list | None = None):
    """
    Run the agent with a user message.
    
    Args:
        agent: The compiled LangGraph agent
        user_message: The user's input message
        conversation_history: Optional list of previous messages for context
    
    Returns:
        The agent's response as a string
    """
    from langchain_core.messages import HumanMessage
    
    # Build the messages list
    messages = conversation_history or []
    messages.append(HumanMessage(content=user_message))
    
    # Run the agent
    result = await agent.ainvoke({"messages": messages})
    
    # Extract the final response
    final_message = result["messages"][-1]
    return final_message.content, result["messages"]

