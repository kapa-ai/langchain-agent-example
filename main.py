#!/usr/bin/env python3
"""
In-Product Agent with Kapa MCP Server

A demo chat interface for the LangGraph agent that combines:
1. Custom tools for subscription and team management
2. Kapa MCP server for product documentation knowledge

Usage:
    python main.py
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def main():
    """Run the interactive chat interface."""
    from src.agent import create_in_product_agent, run_agent
    
    product_name = os.getenv("PRODUCT_NAME", "<Your Product>")
    
    print()
    print("=" * 60)
    print(f"  {product_name} Assistant")
    print("=" * 60)
    print()
    
    print("Initializing agent...")
    print()
    
    try:
        agent = await create_in_product_agent()
    except ValueError as e:
        print(f"Error: {e}")
        print()
        print("Please make sure you have set the following environment variables:")
        print("  - OPENAI_API_KEY")
        print("  - KAPA_MCP_SERVER_URL")
        print("  - KAPA_API_KEY")
        return
    
    # Print introduction
    print(f"👋 Hi! I'm your {product_name} assistant. I can help you with:")
    print()
    print(f"  📊 Subscription & Billing")
    print(f"     Ask about your plan, seats, features, or renewal dates")
    print()
    print(f"  👥 Team Management")
    print(f"     See who's on your team, their roles, and departments")
    print()
    print(f"  📚 Product Questions")
    print(f"     How-to guides, features, troubleshooting, and best practices")
    print()
    print("-" * 60)
    print("Type 'quit' to exit")
    print("-" * 60)
    
    # Chat loop (no memory - each question is independent)
    while True:
        try:
            print()
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGoodbye! 👋")
            break
        
        if not user_input:
            continue
        
        if user_input.lower() in ("quit", "exit", "q"):
            print("\nGoodbye! 👋")
            break
        
        print()
        print("Assistant: ", end="", flush=True)
        
        # Run without conversation history (stateless)
        # Response is streamed directly to stdout
        await run_agent(agent, user_input)


if __name__ == "__main__":
    asyncio.run(main())
