import logging
import time

from openai import OpenAI
from pydantic import BaseModel

from agent.domain.errors import AgentError, ErrorKind
from agent.domain.models import AgentReply, Message, ModelResult, RewriteResult, SearchQuery, Usage
from agent.infrastructure.llm.credentials import Credential
from agent.infrastructure.llm.errors import foundry_errors

log = logging.getLogger(__name__)


class FoundryChatModel:
    """Implementa los puertos ChatModel y QueryRewriter contra Microsoft Foundry (API v1 compatible con OpenAI)."""

    def __init__(
        self,
        endpoint: str,
        credential: Credential,
        deployment: str,
        timeout_s: float,
        max_retries: int,
    ) -> None:
        self.client = OpenAI(
            base_url=f"{endpoint.rstrip('/')}/openai/v1/",
            api_key=credential,
            timeout=timeout_s,
            max_retries=max_retries,
        )
        self.deployment = deployment

    def complete(self, messages: list[Message]) -> ModelResult:
        reply, usage = self._parse(messages, AgentReply)
        return ModelResult(reply=reply, usage=usage)

    def rewrite(self, messages: list[Message]) -> RewriteResult:
        search, usage = self._parse(messages, SearchQuery)
        return RewriteResult(query=search.query, usage=usage)

    def _parse[Output: BaseModel](self, messages: list[Message], schema: type[Output]) -> tuple[Output, Usage]:
        start = time.perf_counter()
        with foundry_errors():
            completion = self.client.chat.completions.parse(
                model=self.deployment, messages=messages, response_format=schema
            )

        message = completion.choices[0].message
        if message.parsed is None:
            raise AgentError(ErrorKind.INVALID_OUTPUT, f"el modelo no devolvió el contrato: {message.refusal or 'vacío'}")

        tokens = completion.usage
        usage = Usage(
            models=[completion.model or self.deployment],
            llm_calls=1,
            latency_ms=int((time.perf_counter() - start) * 1000),
            prompt_tokens=tokens.prompt_tokens if tokens else 0,
            completion_tokens=tokens.completion_tokens if tokens else 0,
        )
        log.info("llm %s %s", schema.__name__, usage.model_dump())
        return message.parsed, usage
