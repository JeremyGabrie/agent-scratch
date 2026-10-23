from fakes import FakeChatModel, FakeEmbedder, FakeKnowledgeBase
from fastapi.testclient import TestClient

from agent.infrastructure.bootstrap import create_app
from agent.infrastructure.config.settings import FoundrySettings, Settings


def test_health():
    settings = Settings(_env_file=None, foundry=FoundrySettings(_env_file=None, auth_provider="api_key"))
    app = create_app(chat_model=FakeChatModel(), settings=settings, embedder=FakeEmbedder(), knowledge_base=FakeKnowledgeBase())
    response = TestClient(app).get("/health")
    assert response.json() == {"status": "ok"}
