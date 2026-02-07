# Subscription Guardian 🛡️

**DevPost / Hackathon Submission**

## 🚀 Project Overview
**Subscription Guardian** is an intelligent AI agent system designed to manage and audit household subscriptions. It acts as a protective layer between your wallet and the recurring billing economy, ensuring that autonomous financial agents don't go rogue.

## 🛑 The Problem
As we delegate more financial tasks to AI, the risk of **autonomous agents exceeding user intent** grows. An agent told to "save money" might cancel your internet connection or a critical service without understanding the context. We need a safety layer—a "Guardian"—that enforces strict policies on what sub-agents can and cannot do.

## 🏗️ Architecture
We use a robust architecture to ensure safety and control:

1.  **User Interface**: **OpenClaw** messaging bot (Telegram/Discord) for natural language interaction.
2.  **Orchestration**: **LangChain** agent that interprets user intent.
3.  **Safety Layer**: **ArmorIQ MCP Server** (Model Context Protocol) that acts as the policy engine, intercepting tool calls.
4.  **Action Layer**: **MCP Servers** that actually interface with subscription APIs (mocked for demo).

**Flow:**
`User` -> `OpenClaw` -> `Agent` -> `Policy Check (ArmorIQ)` -> `Action (or Block)`

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.10+
- OpenAI API Key

### Installation
1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Configure environment variables:
    ```bash
    cp .env.example .env
    # Edit .env with your OPENAI_API_KEY and OPENCLAW_BOT_TOKEN
    ```
4.  Run the main application:
    ```bash
    python main.py
    ```

## 🎮 Demo Scenarios

We have three key scenarios to demonstrate the policy enforcement:

1.  **✅ Allowed Action**:
    *   **User**: "Cancel my Netflix subscription."
    *   **Guardian**: Checks policy "Entertainment under $20/mo can be cancelled autonomously." -> **ALLOWED**.
    *   **Result**: Subscription cancelled.

2.  **🚫 Critical Utility Block**:
    *   **User**: "Cancel the Comcast Internet to save money."
    *   **Guardian**: Checks policy "Critical Utilities (Internet, Power) cannot be cancelled by AI." -> **BLOCKED**.
    *   **Result**: "I cannot cancel the internet; it is flagged as a critical utility."

3.  **🛡️ Dangerous Delegation Block**:
    *   **User**: "Let my roommate Bob have full access to manage my Spotify."
    *   **Guardian**: Checks policy "Credential sharing and delegation to non-admins is prohibited." -> **BLOCKED**.
    *   **Result**: "I cannot delegate access to 'Bob'. Security policy violation."

## 👥 Team Credits
- **[Name]**: Backend & MCP Server
- **[Name]**: Agent Logic & Integration
- **[Name]**: Policy Engine & Prompt Engineering
- **[Name]**: Frontend & Documentation

---
*Built with ❤️ for the [Hackathon Name] 2025.*
