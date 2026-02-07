import yaml
import logging
import os
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass
class PolicyDecision:
    allowed: bool
    reason: str
    action: str
    resource_id: Optional[str] = None
    requester: str = "unknown"
    timestamp: datetime = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "action": self.action,
            "resource_id": self.resource_id,
            "requester": self.requester,
            "timestamp": self.timestamp.isoformat()
        }

class PolicyEngine:
    def __init__(self, config_path="config/policies.yaml"):
        self.config_path = config_path
        self.logger = logging.getLogger("PolicyEngine")
        self.policies = self._load_policies()
        self._audit_log: List[PolicyDecision] = []

    def _load_policies(self) -> Dict[str, Any]:
        """Load policies from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            self.logger.error(f"Failed to load policies: {e}")
            return {}

    def _get_subscription(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve subscription details from mock database."""
        for sub in self.policies.get("mock_database", []):
            if sub["id"] == subscription_id:
                return sub
        return None

    def _log_decision(self, decision: PolicyDecision):
        """Append decision to audit log and system logger."""
        self._audit_log.append(decision)
        status = "ALLOWED" if decision.allowed else "BLOCKED"
        self.logger.info(f"POLICY {status}: {decision.requester} attempted '{decision.action}' on '{decision.resource_id}'. Reason: {decision.reason}")

    def can_cancel(self, subscription_id: str, requester: str = "owner") -> PolicyDecision:
        """Check if a user can cancel a specific subscription."""
        sub = self._get_subscription(subscription_id)
        if not sub:
            decision = PolicyDecision(False, "Subscription not found.", "cancel", subscription_id, requester)
            self._log_decision(decision)
            return decision

        # 1. Check Owner/Global Policies first
        if requester == "owner":
            owner_policies = self.policies.get("owner_policies", {})
            
            # Category Block
            if sub["category"] in owner_policies.get("blocked_categories", []):
                decision = PolicyDecision(
                    False, 
                    f"CATEGORY BLOCK: Cannot cancel '{sub['category']}' subscriptions autonomously.", 
                    "cancel", subscription_id, requester
                )
                self._log_decision(decision)
                return decision

            # Amount Limit
            limit = owner_policies.get("max_cancellation_amount", 0)
            if sub["amount"] > limit:
                decision = PolicyDecision(
                    False, 
                    f"AMOUNT BLOCK: Cost (${sub['amount']}) exceeds cancellation limit (${limit}).", 
                    "cancel", subscription_id, requester
                )
                self._log_decision(decision)
                return decision
            
            decision = PolicyDecision(True, "Action permitted by owner policies.", "cancel", subscription_id, requester)
            self._log_decision(decision)
            return decision

        # 2. Check Delegation Policies
        else:
            # For delegation, cancellation might be strictly prohibited or require specific permissions
            # Using the generic check_delegation for consistency
            return self.check_delegation(requester, "cancel", subscription_id)

    def check_delegation(self, requester: str, action: str, resource_id: str) -> PolicyDecision:
        """Check if a delegated user has permission to perform an action on a resource."""
        sub = self._get_subscription(resource_id)
        if not sub:
            decision = PolicyDecision(False, "Subscription not found.", action, resource_id, requester)
            self._log_decision(decision)
            return decision

        role_policies = self.policies.get("delegation_policies", {}).get(requester)
        if not role_policies:
            decision = PolicyDecision(False, f"No delegation policies defined for user '{requester}'.", action, resource_id, requester)
            self._log_decision(decision)
            return decision

        # Check Expiry
        expiry_str = role_policies.get("expiry_timestamp")
        if expiry_str:
            try:
                expiry_dt = datetime.fromisoformat(expiry_str.replace("Z", "+00:00"))
                # Use timezone-aware comparison if possible, otherwise fallback
                now = datetime.now(expiry_dt.tzinfo)
                if now > expiry_dt:
                    decision = PolicyDecision(False, "DELEGATION BLOCK: Access has expired.", action, resource_id, requester)
                    self._log_decision(decision)
                    return decision
            except ValueError:
                self.logger.warning(f"Invalid expiry timestamp format for {requester}")

        # Check Allowed Subscriptions (Whitelist)
        allowed_subs = [s.lower() for s in role_policies.get("allowed_subscriptions", [])]
        if sub["name"].lower() not in allowed_subs and sub["category"].lower() not in allowed_subs:
            decision = PolicyDecision(
                False, 
                f"DELEGATION BLOCK: User '{requester}' is not authorized to manage '{sub['name']}'.",
                action, resource_id, requester
            )
            self._log_decision(decision)
            return decision

        # For cancellation specifically by delegates, we might want extra checks, 
        # but for now we rely on the whitelist.
        decision = PolicyDecision(True, "Action permitted by delegation policies.", action, resource_id, requester)
        self._log_decision(decision)
        return decision

    def is_within_budget(self, amount: float, category: str, requester: str = "owner") -> PolicyDecision:
        """Check if a spend is within budget limits."""
        # Simple implementation based on global/owner checks or delegation limits
        if requester == "owner":
            # Example: check global confirmation limit
            limit = self.policies.get("global_rules", {}).get("require_confirmation_above", float('inf'))
            if amount > limit:
                 decision = PolicyDecision(False, f"Spend (${amount}) requires manual confirmation (Limit: ${limit}).", "spend", category, requester)
                 self._log_decision(decision)
                 return decision
        else:
            # Check delegation max amount
            role_policies = self.policies.get("delegation_policies", {}).get(requester, {})
            limit = role_policies.get("max_amount", 0)
            if amount > limit:
                decision = PolicyDecision(False, f"Spend (${amount}) exceeds delegate limit (${limit}).", "spend", category, requester)
                self._log_decision(decision)
                return decision

        decision = PolicyDecision(True, "Spend within budget limits.", "spend", category, requester)
        self._log_decision(decision)
        return decision

    def get_all_subscriptions(self) -> List[Dict[str, Any]]:
        return self.policies.get("mock_database", [])
