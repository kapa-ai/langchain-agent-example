"""
Subscription tool for the in-product agent.

This tool simulates fetching subscription information for the current user
from your SaaS product's backend. In a real implementation, this would
call your actual subscription/billing API.
"""

from datetime import datetime, timedelta
from typing import Optional
from langchain_core.tools import tool
from pydantic import BaseModel, Field


class SubscriptionInfo(BaseModel):
    """Schema for subscription information."""
    
    plan_name: str = Field(description="Name of the subscription plan")
    status: str = Field(description="Current status of the subscription")
    seats_used: int = Field(description="Number of seats currently in use")
    seats_total: int = Field(description="Total seats available in the plan")
    billing_cycle: str = Field(description="Billing cycle (monthly/annual)")
    current_period_end: str = Field(description="End date of current billing period")
    monthly_price: float = Field(description="Monthly price in USD")
    features: list[str] = Field(description="List of features included in the plan")


# Simulated subscription data - in a real app, this would come from your database/API
MOCK_SUBSCRIPTION = SubscriptionInfo(
    plan_name="Pro",
    status="active",
    seats_used=8,
    seats_total=10,
    billing_cycle="annual",
    current_period_end=(datetime.now() + timedelta(days=45)).strftime("%Y-%m-%d"),
    monthly_price=49.99,
    features=[
        "Unlimited projects",
        "Advanced analytics",
        "Priority support",
        "Custom integrations",
        "API access",
        "SSO authentication",
    ]
)


@tool
def get_subscription_info(user_id: Optional[str] = None) -> str:
    """
    Get information about the current user's subscription plan.
    
    This tool retrieves details about the subscription including:
    - Plan name and status
    - Seat usage and limits
    - Billing cycle and renewal date
    - Available features
    
    Use this tool when users ask about their subscription, billing,
    plan features, or seat availability.
    
    Args:
        user_id: Optional user ID. If not provided, uses the current session user.
    
    Returns:
        A formatted string with subscription details.
    """
    # In a real implementation, you would:
    # 1. Authenticate the request
    # 2. Look up the user's subscription from your database
    # 3. Return the actual subscription data
    
    sub = MOCK_SUBSCRIPTION
    
    return f"""## Subscription Information

**Plan:** {sub.plan_name}
**Status:** {sub.status.capitalize()}

### Usage
- **Seats:** {sub.seats_used} / {sub.seats_total} used
- **Available seats:** {sub.seats_total - sub.seats_used}

### Billing
- **Cycle:** {sub.billing_cycle.capitalize()}
- **Price:** ${sub.monthly_price}/month (${sub.monthly_price * 12:.2f}/year)
- **Current period ends:** {sub.current_period_end}

### Included Features
{chr(10).join(f'- {feature}' for feature in sub.features)}
"""

