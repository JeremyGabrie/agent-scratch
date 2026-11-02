import pytest

from agent.infrastructure.config.settings import McpAuthProvider, McpSettings
from agent.infrastructure.mcp import auth
from agent.infrastructure.mcp.auth import mcp_bearer


def settings(**values) -> McpSettings:
    return McpSettings(_env_file=None, **values)


def test_static_uses_the_dev_token():
    assert mcp_bearer(settings(auth_provider=McpAuthProvider.STATIC, token="dev-fraud")) == "dev-fraud"


def test_static_requires_a_token():
    with pytest.raises(RuntimeError, match="MCP_TOKEN"):
        mcp_bearer(settings(auth_provider=McpAuthProvider.STATIC))


def test_entra_id_requires_a_scope():
    with pytest.raises(RuntimeError, match="MCP_SCOPE"):
        mcp_bearer(settings(auth_provider=McpAuthProvider.ENTRA_ID))


def test_entra_id_asks_entra_for_the_mcp_scope(monkeypatch):
    asked = []

    class FakeCredential:
        def get_token(self, scope):
            asked.append(scope)
            return type("Token", (), {"token": "entra-token"})()

    monkeypatch.setattr(auth, "DefaultAzureCredential", FakeCredential)
    bearer = mcp_bearer(settings(auth_provider=McpAuthProvider.ENTRA_ID, scope="api://bank-mcp/.default"))
    assert bearer == "entra-token" and asked == ["api://bank-mcp/.default"]


def test_settings_hide_the_mcp_token():
    assert "dev-fraud" not in repr(settings(token="dev-fraud"))
