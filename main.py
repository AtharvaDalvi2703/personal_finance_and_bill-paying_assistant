import os
import time
from dotenv import load_dotenv
from agents.subscription_agent import SubscriptionAgent
from mcp_servers.policy_engine import PolicyEngine
from agents.delegation_agent import DelegatedAgent

# Load environment variables
load_dotenv()

def print_header(title):
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60 + "\n")

def run_owner_scenarios():
    print_header("Owner Scenario: Conversational Agent with Policy Guardrails")
    try:
        agent = SubscriptionAgent()
        print(f"Agent Initialized: {agent.get_role()}")
        print("System: Ready for commands.\n")

        scenarios = [
            ("Checking Subscriptions", "List my active subscriptions."),
            ("Allowed Action (Policy: Cancel < ₹800)", "Cancel my Netflix Premium subscription."),
            ("Blocked Action (Policy: No Utility Cancellation)", "Cancel the JioFiber connection, it's too expensive.")
        ]

        for title, prompt in scenarios:
            print(f"\n--- Scenario: {title} ---")
            print(f"User: {prompt}")
            print("Agent: Thinking...")
            response = agent.process_message(prompt)
            print(f"Agent: {response}\n")
            time.sleep(1)

    except Exception as e:
        print(f"Error initializing Owner Agent: {e}")
        print("Make sure GOOGLE_API_KEY is set in .env")

def run_delegate_scenarios():
    print_header("Delegate Scenario: Bounded Roommate Access")
    
    # Initialize Policy Engine and Delegated Agent
    engine = PolicyEngine()
    roommate_agent = DelegatedAgent(delegator_id="roommate", policy_engine=engine)
    
    print("Delegated Agent: Role = 'roommate'")
    print("Permissions: [Allowed: Spotify, Zomato Gold] [Max Spend: ₹500] [Expiry: 2026]\n")

    # 1. Check Permissions
    print("\n--- Action 1: Check Permissions ---")
    roommate_agent.check_remaining_permissions()

    # 2. Try Allowed Action
    print("\n--- Action 2: Try to Modify Spotify (Allowed) ---")
    roommate_agent.attempt_action("modify", "sub_002") # Spotify Duo

    # 3. Try Blocked Action (Category/Name Block)
    print("\n--- Action 3: Try to Cancel JioFiber (Blocked) ---")
    roommate_agent.attempt_action("cancel", "sub_003") # JioFiber

    # 4. Try Blocked Action (Spend Limit)
    print("\n--- Action 4: Try to Spend ₹2000 on New Sub (Blocked) ---")
    roommate_agent.attempt_action("spend", "sub_new", amount=2000.0, category="streaming")

def main():
    while True:
        print_header("Subscription Guardian - India Edition Hackathon Demo")
        print("1. Run Owner Scenarios (LangChain + Gemini + MCP)")
        print("2. Run Delegate Scenarios (Direct Policy Engine + Bounded Agent)")
        print("3. Exit")
        
        choice = input("\nSelect an option (1-3): ")
        
        if choice == '1':
            run_owner_scenarios()
        elif choice == '2':
            run_delegate_scenarios()
        elif choice == '3':
            print("\nExiting. Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()
