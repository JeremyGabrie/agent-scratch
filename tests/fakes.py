"""Implementaciones de prueba de los puertos ChatModel y Embedder: sin red ni Foundry."""

from agent.domain.errors import AgentError, ErrorKind
from agent.domain.models import AgentReply, Intent, Message, ModelResult, Usage


class FakeChatModel:
    # ponytail: heurística naive por palabras clave, solo para tests
    RULES = [
        (Intent.ACCION_SENSIBLE, ("bloque", "robaron", "robo", "perdí", "registrar reclamo")),
        (Intent.CONSULTA_DATOS, ("mis movimientos", "estado de mi reclamo", "estado del reclamo")),
        (Intent.CONSULTA_PRODUCTO, ("fraude", "contracargo", "plazo", "reclamo", "no reconozco")),
        (Intent.SALUDO, ("hola", "buenos", "buenas", "gracias", "adiós")),
    ]

    def complete(self, messages: list[Message]) -> ModelResult:
        text = messages[-1]["content"].lower()
        intent = next((i for i, words in self.RULES if any(w in text for w in words)), Intent.FUERA_DE_ALCANCE)
        reply = AgentReply(intent=intent, answer=f"[fake] intención detectada: {intent}")
        usage = Usage(models=["fake"], llm_calls=1, prompt_tokens=10, completion_tokens=5)
        return ModelResult(reply=reply, usage=usage)


class RecordingChatModel(FakeChatModel):
    def __init__(self) -> None:
        self.calls: list[list[Message]] = []

    def complete(self, messages: list[Message]) -> ModelResult:
        self.calls.append(messages)
        return super().complete(messages)


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
