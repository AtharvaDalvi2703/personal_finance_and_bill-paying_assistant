from fastmcp import FastMCP, Context
import logging
from mcp_servers.policy_engine import PolicyEngine

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SubscriptionMCP")

# Initialize Policy Engine
policy_engine = PolicyEngine()

# Create MCP Server
mcp = FastMCP("Subscription Guardian Server")

@mcp.tool()
def list_subscriptions(ctx: Context) -> list[dict]:
    """
    List all active subscriptions.
    
    Returns:
        list[dict]: A list of subscription objects.
    """
    subs = policy_engine.get_all_subscriptions()
    logger.info(f"Listed {len(subs)} subscriptions.")
    return subs

@mcp.tool()
def cancel_subscription(ctx: Context, subscription_id: str, user_role: str = "owner") -> dict:
    """
    Attempt to cancel a subscription, subject to policy enforcement.

    Args:
        subscription_id (str): The ID of the subscription to cancel.
        user_role (str, optional): The role of the user attempting the action. Defaults to "owner".

    Returns:
        dict: Result of the action, including success status and reason.
    """
    logger.info(f"Received request to cancel subscription {subscription_id} by {user_role}")
    
    # Policy Check
    policy_result = policy_engine.evaluate_action("cancel", {
        "subscription_id": subscription_id, 
        "user_role": user_role
    })
    
    if not policy_result.get("allowed"):
        logger.warning(f"BLOCKED: Cancellation of {subscription_id} denied. Reason: {policy_result.get('reason')}")
        return {
            "status": "blocked",
            "reason": policy_result.get("reason"),
            "subscription_id": subscription_id
        }

    # Execute Action (Mock)
    logger.info(f"SUCCESS: Cancelled subscription {subscription_id}")
    return {
        "status": "success",
        "message": f"Subscription {subscription_id} has been successfully cancelled.",
        "subscription_id": subscription_id
    }

@mcp.tool()
def check_delegation_authority(ctx: Context, user_role: str, subscription_id: str) -> dict:
    """
    Check if a delegated user (e.g., roommate) has authority over a specific subscription.
    
    Args:
        user_role (str): The role of the user (e.g., "roommate").
        subscription_id (str): The ID of the subscription to check.
        
    Returns:
        dict: Authority status and explanation.
    """
    policy_result = policy_engine.evaluate_action("access", {
        "subscription_id": subscription_id, 
        "user_role": user_role
    })
    
    return {
        "authorized": policy_result.get("allowed"),
        "reason": policy_result.get("reason", "Policy check completed.")
    }

if __name__ == "__main__":
    mcp.run()
