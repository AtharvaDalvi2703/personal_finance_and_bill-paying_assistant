from fastmcp import FastMCP

mcp = FastMCP("Subscription Server")

@mcp.tool()
def get_subscriptions():
    """Get list of active subscriptions."""
    return [{"name": "Netflix", "cost": 15.99}, {"name": "Spotify", "cost": 9.99}]

if __name__ == "__main__":
    mcp.run()
