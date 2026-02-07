import logging
from typing import List, Dict, Any
from mcp_servers.policy_engine import PolicyEngine

class DelegatedAgent:
    """
    An agent acting on behalf of another user (e.g., roommate) with restricted permissions.
    Demonstrates bounded delegation where actions are strictly limited by policy.
    """
    def __init__(self, delegator_id: str, policy_engine: PolicyEngine):
        self.delegator_id = delegator_id
        self.policy_engine = policy_engine
        self.logger = logging.getLogger(f"DelegatedAgent-{delegator_id}")
        self.logger.info(f"Initialized DelegatedAgent for '{delegator_id}'")

    def attempt_action(self, action: str, resource_id: str, **kwargs) -> Dict[str, Any]:
        """
        Attempt to perform an action on a resource.
        The action is first validated against the policy engine.
        """
        self.logger.info(f"Attempting action '{action}' on '{resource_id}'...")

        # 1. Check Permissions
        if action == "cancel":
            decision = self.policy_engine.can_cancel(resource_id, requester=self.delegator_id)
        elif action == "spend":
            amount = kwargs.get("amount", 0)
            category = kwargs.get("category", "unknown")
            decision = self.policy_engine.is_within_budget(amount, category, requester=self.delegator_id)
        else:
            # Generic delegation check
            decision = self.policy_engine.check_delegation(self.delegator_id, action, resource_id)

        # 2. Enforce Decision
        if not decision.allowed:
            self.logger.warning(f"ACTION BLOCKED: {decision.reason}")
            return {
                "status": "blocked",
                "reason": decision.reason,
                "action": action,
                "resource_id": resource_id
            }

        # 3. Execute Action (Simulated)
        # In a real system, this would call the MCP server tool or API.
        self.logger.info(f"ACTION ALLOWED: Executing '{action}' on '{resource_id}'.")
        return {
            "status": "success",
            "message": f"Successfully executed '{action}' on '{resource_id}'.",
            "details": f"Authorized by policy: {decision.reason}"
        }

    def check_remaining_permissions(self) -> List[str]:
        """
        Check what this agent is allowed to access based on current policy.
        """
        allowed_resources = []
        all_subs = self.policy_engine.get_all_subscriptions()
        
        for sub in all_subs:
            # Check if we can 'modify' or 'access' this subscription
            decision = self.policy_engine.check_delegation(self.delegator_id, "access", sub["id"])
            if decision.allowed:
                allowed_resources.append(f"{sub['name']} ({sub['category']})")
        
        self.logger.info(f"Remaining permissions for '{self.delegator_id}': {allowed_resources}")
        return allowed_resources

    def refresh_delegation(self):
        """
        Refresh policy rules (reload from source).
        """
        self.logger.info("Refreshing delegation policies...")
        # Since PolicyEngine loads from file on init, we might need a reload method there.
        # For now, we assume policies are static or re-instantiating engine.
        # But we can reload the internal policies dict of the engine.
        self.policy_engine.policies = self.policy_engine._load_policies()
        self.logger.info("Policies refreshed.")
