from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

# --- 1. THE VAULT (MOCK DATABASE) ---
BALANCE = 50000
ALLOWED_MERCHANTS = ["Adani Electricity",
                     "Jio Fiber", "HDFC Credit Card", "Netflix"]
TRANSACTION_HISTORY = []

# --- 2. THE GUARDRAILS (SECURITY POLICY) ---
MAX_TX_LIMIT = 5000  # Max per transaction

# --- 3. CREATE THE OFFICIAL MCP SERVER ---
# This "registers" your server so Laptop 1 can discover it.
mcp = FastMCP("PersonalFinanceVault")

# --- 4. THE TOOLS (CAPABILITIES) ---


@mcp.tool()
def get_balance() -> str:
    """Returns the current bank balance."""
    return f"Your current balance is ₹{BALANCE}"


@mcp.tool()
def get_transaction_history() -> list:
    """Returns a list of all successful past transactions."""
    return TRANSACTION_HISTORY


@mcp.tool()
def pay_bill(merchant: str, amount: float, intent_token: str = "REQUIRED") -> str:
    """
    Pays a bill to a specific merchant. 
    Requires a valid ArmorIQ Intent Token for authorization.
    """
    global BALANCE

    # SECURITY CHECK 1: Verify Intent Token presence (Official Requirement)
    if intent_token == "REQUIRED":
        return "ERROR: Unauthorized. No ArmorIQ Intent Token detected."

    # SECURITY CHECK 2: Merchant Allowlist
    if merchant not in ALLOWED_MERCHANTS:
        return f"REJECTED: Merchant '{merchant}' is not authorized. Transaction blocked."

    # SECURITY CHECK 3: Transaction Safety Limit
    if amount > MAX_TX_LIMIT:
        return f"REJECTED: Amount ₹{amount} exceeds your safety limit of ₹{MAX_TX_LIMIT}."

    # SECURITY CHECK 4: Sufficient Funds
    if amount > BALANCE:
        return f"ERROR: Insufficient funds. Current balance: ₹{BALANCE}"

    # EXECUTION: Only happens if all guards pass
    BALANCE -= amount
    receipt = f"SUCCESS: Paid ₹{amount} to {merchant}. New Balance: ₹{BALANCE}"
    TRANSACTION_HISTORY.append(receipt)
    return receipt


# --- 5. MOUNT TO FASTAPI FOR SSE SUPPORT ---
# This allows Laptop 1 to connect to you over a network (ngrok).
app = FastAPI()
app.mount("/", mcp.sse_app())

if __name__ == "__main__":
    import uvicorn
    # Laptop 2 starts listening on port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)
