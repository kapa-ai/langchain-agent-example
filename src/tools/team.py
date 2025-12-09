"""
Team members tool for the in-product agent.

This tool simulates fetching team member information from your SaaS product's
backend. In a real implementation, this would call your actual team/user
management API.
"""

from datetime import datetime, timedelta
from typing import Optional
from langchain_core.tools import tool
from pydantic import BaseModel, Field


class TeamMember(BaseModel):
    """Schema for a team member."""
    
    id: str = Field(description="Unique identifier for the team member")
    name: str = Field(description="Full name of the team member")
    email: str = Field(description="Email address")
    role: str = Field(description="Role in the organization (admin, member, viewer)")
    department: str = Field(description="Department or team")
    joined_date: str = Field(description="Date when the member joined")
    last_active: str = Field(description="Last activity timestamp")
    status: str = Field(description="Current status (active, invited, deactivated)")


# Simulated team data - in a real app, this would come from your database/API
MOCK_TEAM_MEMBERS = [
    TeamMember(
        id="usr_001",
        name="Sarah Chen",
        email="sarah.chen@acme.com",
        role="admin",
        department="Engineering",
        joined_date="2023-01-15",
        last_active=(datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M"),
        status="active"
    ),
    TeamMember(
        id="usr_002",
        name="Marcus Johnson",
        email="marcus.j@acme.com",
        role="admin",
        department="Product",
        joined_date="2023-02-20",
        last_active=(datetime.now() - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M"),
        status="active"
    ),
    TeamMember(
        id="usr_003",
        name="Emily Rodriguez",
        email="emily.r@acme.com",
        role="member",
        department="Engineering",
        joined_date="2023-04-10",
        last_active=(datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"),
        status="active"
    ),
    TeamMember(
        id="usr_004",
        name="James Wilson",
        email="james.w@acme.com",
        role="member",
        department="Design",
        joined_date="2023-06-05",
        last_active=(datetime.now() - timedelta(hours=12)).strftime("%Y-%m-%d %H:%M"),
        status="active"
    ),
    TeamMember(
        id="usr_005",
        name="Priya Patel",
        email="priya.p@acme.com",
        role="member",
        department="Engineering",
        joined_date="2023-08-22",
        last_active=(datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M"),
        status="active"
    ),
    TeamMember(
        id="usr_006",
        name="Alex Kim",
        email="alex.k@acme.com",
        role="viewer",
        department="Marketing",
        joined_date="2023-10-01",
        last_active=(datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d %H:%M"),
        status="active"
    ),
    TeamMember(
        id="usr_007",
        name="Jordan Lee",
        email="jordan.l@acme.com",
        role="member",
        department="Sales",
        joined_date="2024-01-08",
        last_active=(datetime.now() - timedelta(hours=8)).strftime("%Y-%m-%d %H:%M"),
        status="active"
    ),
    TeamMember(
        id="usr_008",
        name="Taylor Swift",
        email="taylor.s@acme.com",
        role="viewer",
        department="Finance",
        joined_date="2024-03-15",
        last_active="N/A",
        status="invited"
    ),
]


@tool
def get_team_members(
    role_filter: Optional[str] = None,
    department_filter: Optional[str] = None,
    include_inactive: bool = False
) -> str:
    """
    Get information about team members in the organization.
    
    This tool retrieves a list of team members with their roles, departments,
    and activity status. You can filter by role or department.
    
    Use this tool when users ask about:
    - Who is on their team
    - Team member roles and permissions
    - Department assignments
    - Recent team activity
    - Pending invitations
    
    Args:
        role_filter: Optional filter by role (admin, member, viewer)
        department_filter: Optional filter by department name
        include_inactive: Whether to include deactivated members (default: False)
    
    Returns:
        A formatted string with team member information.
    """
    # In a real implementation, you would:
    # 1. Authenticate the request
    # 2. Query your user/team database with the filters
    # 3. Return the actual team data
    
    members = MOCK_TEAM_MEMBERS
    
    # Apply filters
    if role_filter:
        members = [m for m in members if m.role.lower() == role_filter.lower()]
    
    if department_filter:
        members = [m for m in members if department_filter.lower() in m.department.lower()]
    
    if not include_inactive:
        members = [m for m in members if m.status != "deactivated"]
    
    if not members:
        return "No team members found matching the specified criteria."
    
    # Group by role for better organization
    admins = [m for m in members if m.role == "admin"]
    regular_members = [m for m in members if m.role == "member"]
    viewers = [m for m in members if m.role == "viewer"]
    
    def format_member(m: TeamMember) -> str:
        status_icon = "✓" if m.status == "active" else "⏳" if m.status == "invited" else "✗"
        return f"  - **{m.name}** ({m.email}) {status_icon}\n    {m.department} · Last active: {m.last_active}"
    
    result = f"## Team Members ({len(members)} total)\n\n"
    
    if admins:
        result += "### Admins\n"
        result += "\n".join(format_member(m) for m in admins) + "\n\n"
    
    if regular_members:
        result += "### Members\n"
        result += "\n".join(format_member(m) for m in regular_members) + "\n\n"
    
    if viewers:
        result += "### Viewers\n"
        result += "\n".join(format_member(m) for m in viewers) + "\n\n"
    
    # Add summary
    invited_count = sum(1 for m in members if m.status == "invited")
    if invited_count:
        result += f"\n*{invited_count} pending invitation(s)*"
    
    return result

