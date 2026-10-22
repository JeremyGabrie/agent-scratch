from uuid import uuid4

from fastapi import APIRouter

from agent.application.chat_service import ChatService
from agent.infrastructure.api.schemas import ChatRequest, ChatResponse


def build_router(chat_service: ChatService) -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    # TODO S2: handler de AgentError → HTTP: timeout 504, rate limit 429, salida inválida 502.
    @router.post("/chat")
    def chat(req: ChatRequest) -> ChatResponse:
        session_id = req.session_id or uuid4()
        reply = chat_service.handle(str(session_id), req.message)
        return ChatResponse(session_id=session_id, intent=reply.intent, answer=reply.answer)

    return router
