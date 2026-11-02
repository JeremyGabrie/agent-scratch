from azure.identity import DefaultAzureCredential

from agent.infrastructure.config.settings import McpAuthProvider, McpSettings


def mcp_bearer(mcp: McpSettings) -> str:
    """El token que el agente presenta al servidor MCP. De él depende qué tools ve: solo las de su dominio."""
    match mcp.auth_provider:
        case McpAuthProvider.STATIC:
            if not mcp.token.get_secret_value():
                raise RuntimeError("MCP_AUTH_PROVIDER=static requiere MCP_TOKEN en .env (dev-<tu dominio>)")
            return mcp.token.get_secret_value()
        case McpAuthProvider.ENTRA_ID:
            if not mcp.scope:
                raise RuntimeError("MCP_AUTH_PROVIDER=entra_id requiere MCP_SCOPE en .env (el de tu ficha)")
            # az login en local, Managed Identity desplegado: el mismo DefaultAzureCredential que Foundry y AI Search
            return DefaultAzureCredential().get_token(mcp.scope).token
