import os
import yaml
import logging
from typing import List, Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage
from langchain_core.tools import tool, StructuredTool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor, create_tool_calling_agent

# Import MCP Server functions directly for this local integration
from mcp_servers.subscription_server import list_subscriptions, cancel_subscription, check_delegation_authority
from fastmcp import Context

# Mock Context for local function calls since we aren't running over HTTP yet
class MockContext(Context):
    def __init__(self):
        pass

mock_ctx = MockContext()

class SubscriptionAgent:
    def __init__(self, config_path="config/agent_config.yaml"):
        self.logger = logging.getLogger("SubscriptionAgent")
        self.config = self._load_config(config_path)
        self.llm = self._setup_llm()
        self.tools = self._setup_tools()
        self.agent_executor = self._setup_agent()

    def _load_config(self, path):
        with open(path, 'r') as f:
            return yaml.safe_load(f)

    def _setup_llm(self):
        agent_conf = self.config['agent']
        # Ensure GOOGLE_API_KEY is set in environment
        if "GOOGLE_API_KEY" not in os.environ:
            self.logger.warning("GOOGLE_API_KEY not found in environment variables.")
        
        return ChatGoogleGenerativeAI(
            model=agent_conf.get('model', 'gemini-1.5-flash'),
            temperature=agent_conf.get('temperature', 0.3),
            max_tokens=agent_conf.get('max_tokens', 2000),
            convert_system_message_to_human=True # Sometimes needed for Gemini compatibility
        )

    def _setup_tools(self) -> List[StructuredTool]:
        """
        Wrap MCP server functions as LangChain tools.
        In a real distributed MCP setup, this would discover tools via the MCP protocol.
        Here we wrap the python functions directly.
        """
        
        @tool
        def tool_list_subscriptions() -> str:
            """List all active subscriptions and their details."""
            subs = list_subscriptions(mock_ctx)
            return str(subs)

        @tool
        def tool_cancel_subscription(subscription_id: str, user_role: str = "owner") -> str:
            """
            Cancel a specific subscription.
            Args:
                subscription_id: The ID of the subscription to cancel.
                user_role: The role of the user requesting cancellation (default: owner).
            """
            result = cancel_subscription(mock_ctx, subscription_id, user_role)
            if result['status'] == 'blocked':
                return f"ACTION BLOCKED: {result['reason']}"
            return f"SUCCESS: {result.get('message', 'Subscription cancelled')}"

        @tool
        def tool_check_delegation(user_role: str, subscription_id: str) -> str:
            """Check if a delegated user has authority over a subscription."""
            result = check_delegation_authority(mock_ctx, user_role, subscription_id)
            status = "AUTHORIZED" if result['authorized'] else "UNAUTHORIZED"
            return f"{status}: {result['reason']}"

        return [tool_list_subscriptions, tool_cancel_subscription, tool_check_delegation]

    def _setup_agent(self):
        system_prompt = self.config['agent']['system_prompt']
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = create_tool_calling_agent(self.llm, self.tools, prompt)
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True)

    def process_message(self, user_input: str, chat_history: List[BaseMessage] = []) -> str:
        """
        Process a user message and return the agent's response.
        """
        self.logger.info(f"Processing message: {user_input}")
        
        try:
            response = self.agent_executor.invoke({
                "input": user_input,
                "chat_history": chat_history
            })
            return response["output"]
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return f"I encountered an error while processing your request: {str(e)}"

    def get_role(self) -> str:
        return self.config['agent']['role']
