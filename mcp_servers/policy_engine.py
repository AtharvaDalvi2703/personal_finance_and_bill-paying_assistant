import yaml
import logging
import os
from datetime import datetime

class PolicyEngine:
    def __init__(self, config_path="config/policies.yaml"):
        self.config_path = config_path
        self.output_dir = os.path.dirname(config_path)
        self.logger = logging.getLogger("PolicyEngine")
        self.policies = self._load_policies()
        
    def _load_policies(self):
        """Load policies from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            self.logger.error(f"Failed to load policies: {e}")
            return {}

    def _get_subscription(self, subscription_id):
        """Retrieve subscription details from mock database."""
        for sub in self.policies.get("mock_database", []):
            if sub["id"] == subscription_id:
                return sub
        return None

    def evaluate_action(self, action, context):
        """
        Evaluate if an action is allowed based on policies.
        
        Args:
            action (str): The action to perform (e.g., "cancel", "modify").
            context (dict): Context for the action (e.g., user_role, subscription_id).
            
        Returns:
            dict: {"allowed": bool, "reason": str}
        """
        user_role = context.get("user_role", "owner")
        subscription_id = context.get("subscription_id")
        
        # Log the evaluation request
        self.logger.info(f"Evaluating action '{action}' for role '{user_role}' on subscription '{subscription_id}'")

        if user_role == "owner":
            return self._evaluate_owner_policies(action, subscription_id)
        elif user_role in self.policies.get("delegation_policies", {}):
            return self._evaluate_delegation_policies(user_role, action, subscription_id)
        else:
            return {"allowed": False, "reason": f"Unknown user role: {user_role}"}

    def _evaluate_owner_policies(self, action, subscription_id):
        """Evaluate policies for the owner."""
        sub = self._get_subscription(subscription_id)
        if not sub:
            return {"allowed": False, "reason": "Subscription not found."}

        owner_policies = self.policies.get("owner_policies", {})
        
        if action == "cancel":
            # Check blocked categories (CRITICAL SAFETY CHECK)
            if sub["category"] in owner_policies.get("blocked_categories", []):
                return {
                    "allowed": False, 
                    "reason": f"CATEGORY BLOCK: Cannot cancel '{sub['category']}' subscriptions autonomously."
                }
            
            # Check cancellation amount limit
            limit = owner_policies.get("max_cancellation_amount", 0)
            if sub["amount"] > limit:
                return {
                    "allowed": False, 
                    "reason": f"AMOUNT BLOCK: Subscription cost (${sub['amount']}) exceeds autonomous cancellation limit (${limit})."
                }

        return {"allowed": True, "reason": "Action permitted by owner policies."}

    def _evaluate_delegation_policies(self, role, action, subscription_id):
        """Evaluate policies for delegated users (e.g., roommate)."""
        sub = self._get_subscription(subscription_id)
        if not sub:
            return {"allowed": False, "reason": "Subscription not found."}

        role_policies = self.policies.get("delegation_policies", {}).get(role, {})
        
        # Check allowed subscriptions (whitelist)
        # Convert both to lowercase for case-insensitive comparison
        allowed_subs = [s.lower() for s in role_policies.get("allowed_subscriptions", [])]
        if sub["name"].lower() not in allowed_subs and sub["category"].lower() not in allowed_subs:
             return {
                "allowed": False, 
                "reason": f"DELEGATION BLOCK: User '{role}' is not authorized to manage '{sub['name']}'."
            }

        # Check expiry
        expiry_str = role_policies.get("expiry_timestamp")
        if expiry_str:
            expiry_dt = datetime.fromisoformat(expiry_str.replace("Z", "+00:00"))
            if datetime.now(expiry_dt.tzinfo) > expiry_dt:
                return {"allowed": False, "reason": "DELEGATION BLOCK: Access has expired."}

        return {"allowed": True, "reason": "Action permitted by delegation policies."}
    
    def get_all_subscriptions(self):
        return self.policies.get("mock_database", [])
