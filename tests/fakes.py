"""Implementaciones de prueba del puerto ChatModel: sin red ni Foundry."""

from agent.domain.models import AgentReply, Intent, Message


class FakeChatModel:
    # ponytail: heurística naive por palabras clave, solo para tests
    RULES = [
        (Intent.ACCION_SENSIBLE, ("bloque", "robaron", "robo", "perdí", "registrar reclamo")),
        (Intent.CONSULTA_DATOS, ("mis movimientos", "estado de mi reclamo", "estado del reclamo")),
        (Intent.CONSULTA_PRODUCTO, ("fraude", "contracargo", "plazo", "reclamo", "no reconozco")),
        (Intent.SALUDO, ("hola", "buenos", "buenas", "gracias", "adiós")),
    ]

    def complete(self, messages: list[Message]) -> AgentReply:
        text = messages[-1]["content"].lower()
        intent = next((i for i, words in self.RULES if any(w in text for w in words)), Intent.FUERA_DE_ALCANCE)
        return AgentReply(intent=intent, answer=f"[fake] intención detectada: {intent}")


class RecordingChatModel(FakeChatModel):
    def __init__(self) -> None:
        self.calls: list[list[Message]] = []

    def complete(self, messages: list[Message]) -> AgentReply:
        self.calls.append(messages)
        return super().complete(messages)
