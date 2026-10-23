"""Implementaciones de prueba de los puertos: sin red, Foundry ni base vectorial."""

from agent.domain.errors import AgentError, ErrorKind
from agent.domain.knowledge import Chunk, SearchHit
from agent.domain.models import AgentReply, Intent, Message, ModelResult, RewriteResult, Usage


class FakeChatModel:
    # ponytail: heurística naive por palabras clave, solo para tests
    RULES = [
        (Intent.ACCION_SENSIBLE, ("bloque", "robaron", "robo", "perdí", "registrar reclamo")),
        (Intent.CONSULTA_DATOS, ("mis movimientos", "estado de mi reclamo", "estado del reclamo")),
        (Intent.CONSULTA_PRODUCTO, ("fraude", "contracargo", "plazo", "reclamo", "no reconozco")),
        (Intent.SALUDO, ("hola", "buenos", "buenas", "gracias", "adiós")),
    ]

    def __init__(self, fuentes: list[int] | None = None) -> None:
        self.fuentes = fuentes or []  # los números de fragmento que "cita" en cada respuesta

    def complete(self, messages: list[Message]) -> ModelResult:
        text = messages[-1]["content"].lower()
        intent = next((i for i, words in self.RULES if any(w in text for w in words)), Intent.FUERA_DE_ALCANCE)
        reply = AgentReply(intent=intent, answer=f"[fake] intención detectada: {intent}", fuentes=self.fuentes)
        usage = Usage(models=["fake"], llm_calls=1, prompt_tokens=10, completion_tokens=5)
        return ModelResult(reply=reply, usage=usage)

    def rewrite(self, messages: list[Message]) -> RewriteResult:
        usage = Usage(models=["fake"], llm_calls=1, prompt_tokens=8, completion_tokens=4)
        return RewriteResult(query=f"[reescrita] {messages[-1]['content']}", usage=usage)


class RecordingChatModel(FakeChatModel):
    def __init__(self, fuentes: list[int] | None = None) -> None:
        super().__init__(fuentes)
        self.calls: list[list[Message]] = []
        self.rewrites: list[list[Message]] = []

    def complete(self, messages: list[Message]) -> ModelResult:
        self.calls.append(messages)
        return super().complete(messages)

    def rewrite(self, messages: list[Message]) -> RewriteResult:
        self.rewrites.append(messages)
        return super().rewrite(messages)


class FailingChatModel:
    def __init__(self, kind: ErrorKind) -> None:
        self.kind = kind

    def complete(self, messages: list[Message]) -> ModelResult:
        raise AgentError(self.kind, "falla simulada")


class FakeEmbedder:
    DIM = 8

    def __init__(self) -> None:
        self.calls: list[int] = []

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(len(texts))
        return [[float(len(t))] * self.DIM for t in texts]


class FakeKnowledgeBase:
    """Devuelve siempre los mismos chunks, en orden, y anota qué se buscó."""

    def __init__(self, chunks: list[Chunk] | None = None) -> None:
        self.chunks = chunks or []
        self.queries: list[str] = []

    def publish(self, chunks: list[Chunk]) -> None:
        self.chunks = chunks

    def count(self) -> int:
        return len(self.chunks)

    def search(self, text: str, vector: list[float], top_k: int) -> list[SearchHit]:
        self.queries.append(text)
        return [SearchHit(chunk=chunk, score=1.0) for chunk in self.chunks[:top_k]]
