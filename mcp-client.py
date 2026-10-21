# client.py
import asyncio
import os
import httpx
from fastmcp.client import Client as FastMCPClient
from langchain.mcp import MCPAdapter
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

os.environ["OPENAI_API_KEY"] = "your-openai-api-key"

class OAuth2BearerAuth(httpx.Auth):
    """Automatically stamps the active enterprise cryptographic JWT onto all outgoing MCP signals."""
    def __init__(self, token: str):
        self.token = token

    def auth_flow(self, request: httpx.Request):
        request.headers["Authorization"] = f"Bearer {self.token}"
        yield request

async def run_enterprise_workflow(active_user_jwt: str):
    server_url = "http://127.0.0"
    
    # Bind network layers directly to our enterprise token adapter
    auth_handler = OAuth2BearerAuth(token=active_user_jwt)
    mcp_client = FastMCPClient(server_url, auth=auth_handler)
    
    async with MCPAdapter(mcp_client) as adapter:
        tools = await adapter.list_tools()
        model = ChatOpenAI(model="gpt-4o", temperature=0)
        agent = create_react_agent(model, tools=tools)
        
        inputs = {"messages": [("user", "Fetch financial ledgers for account ACC-4920.")]}
        response = await agent.ainvoke(inputs)
        print("\n--- Final Agent Execution Response ---")
        print(response["messages"][-1].content)

if __name__ == "__main__":
    # In production, this token is received after logging into Auth0/Cognito via your app UI
    MOCK_ENTERPRISE_JWT = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ii4uLiJ9.eyJpc3MiOiJodHRwczovL..."
    
    asyncio.run(run_enterprise_workflow(active_user_jwt=MOCK_ENTERPRISE_JWT))
