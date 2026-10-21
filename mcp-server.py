# server.py
import uvicorn
import jwt
import requests
from fastapi import FastAPI, Request, HTTPException, status
from fastmcp import FastMCP
from pydantic import BaseModel

app = FastAPI(title="Enterprise Production MCP Server")
mcp = FastMCP("EnterpriseSecureServer")

# --- Enterprise Configuration Configurations (Replace with your actual values) ---
# For Auth0:   https://YOUR_://auth0.com
# For Cognito: https://cognito-idp.YOUR_REGION://
IDP_ISSUER = "https://auth0.com" 
AUDIENCE = "https://yourcompany.com"
JWKS_URL = f"{IDP_ISSUER}.well-known/jwks.json"

# Fetch public cryptographic keys from IdP to verify token signatures asynchronously
jwks_client = jwt.PyJWKClient(JWKS_URL)

def verify_enterprise_jwt(request: Request, required_scope: str) -> dict:
    """Decodes, verifies signature, check expiration, and validates OAuth scopes."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header.")
    
    token = auth_header.split(" ")[1]
    
    try:
        # 1. Fetch the exact public signing key that matches the token header 'kid'
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        
        # 2. Cryptographically verify signature, issuer, audience, and expiration date (exp)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=AUDIENCE,
            issuer=IDP_ISSUER
        )
        
        # 3. OAuth2 Authorization: Verify required permissions/scopes inside the claims payload
        scopes = payload.get("scope", "").split()
        if required_scope not in scopes:
            raise HTTPException(
                status_code=403, 
                detail=f"Forbidden: Insufficient privileges. Requires '{required_scope}' scope."
            )
            
        return payload  # Contains validated user claims (email, metadata, roles)
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Authentication failed: Token expired.")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

class DataInput(BaseModel):
    account_id: str

@mcp.tool()
async def fetch_financial_ledger(arguments: DataInput) -> str:
    """High-security ledger fetch tool. Requires 'read:financials' OAuth scope."""
    from fastmcp.server.dependencies import get_http_request
    request = get_http_request()
    
    # Securely authorize request via the OIDC token
    token_claims = verify_enterprise_jwt(request, required_scope="read:financials")
    
    return f"Authorized payload access granted for User sub: {token_claims['sub']}. Data compiled successfully."

app.mount("/mcp", mcp.sse_app())

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
