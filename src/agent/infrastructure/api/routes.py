import logging
from uuid import uuid4

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from agent.application.chat_service import ChatService
from agent.domain.errors import AgentError, ErrorKind
from agent.infrastructure.api.schemas import ChatRequest, ChatResponse, ErrorResponse

log = logging.getLogger(__name__)

ERROR_STATUS = {
    ErrorKind.TIMEOUT: 504,
    ErrorKind.RATE_LIMIT: 429,
    ErrorKind.INVALID_OUTPUT: 502,
    ErrorKind.UPSTREAM: 502,
}
ERROR_RESPONSES = {status: {"model": ErrorResponse} for status in set(ERROR_STATUS.values())}


async def agent_error_handler(request: Request, exc: AgentError) -> JSONResponse:
    log.warning("%s %s falló: %s", request.method, request.url.path, exc, exc_info=exc.__cause__)
    body = ErrorResponse(error=exc.kind, detail=exc.detail)
    return JSONResponse(status_code=ERROR_STATUS[exc.kind], content=body.model_dump(mode="json"))


def build_router(chat_service: ChatService) -> APIRouter:
    router = APIRouter()

    @router.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @router.post("/chat", responses=ERROR_RESPONSES)
    def chat(req: ChatRequest) -> ChatResponse:
        session_id = req.session_id or uuid4()
        turn = chat_service.handle(str(session_id), req.message)
        return ChatResponse(
            session_id=session_id, intent=turn.reply.intent, answer=turn.reply.answer, usage=turn.usage
        )

    return router
