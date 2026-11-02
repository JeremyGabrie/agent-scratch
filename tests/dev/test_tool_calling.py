"""El ciclo de dev/mcp/tool_calling.py con un modelo falso que sigue un guion: sin Foundry, contra el mock MCP en memoria."""

import asyncio
import json
from types import SimpleNamespace

from fastmcp import Client
from mock_mcp import create_server
from openai.types.chat import ChatCompletion
from tool_calling import MAX_TURNS, answer


def wants(name: str, **arguments) -> ChatCompletion:
    """Una respuesta del modelo que pide una tool."""
    call = {"id": f"call-{name}", "type": "function", "function": {"name": name, "arguments": json.dumps(arguments)}}
    return completion({"role": "assistant", "content": None, "tool_calls": [call]})


def says(text: str) -> ChatCompletion:
    return completion({"role": "assistant", "content": text})


def completion(message: dict) -> ChatCompletion:
    return ChatCompletion.model_validate({"id": "x", "object": "chat.completion", "created": 0, "model": "fake",
                                          "choices": [{"index": 0, "finish_reason": "stop", "message": message}]})


class ScriptedModel:
    """Devuelve las respuestas en orden (la última se repite) y guarda los mensajes que recibió en cada llamada."""

    def __init__(self, *replies: ChatCompletion) -> None:
        self.replies, self.received = list(replies), []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def create(self, model: str, messages: list[dict], tools: list[dict]) -> ChatCompletion:
        self.received.append([dict(message) for message in messages])
        return self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]


def run(model: ScriptedModel, client: Client | None = None) -> str:
    async def go(client: Client) -> str:
        async with client:
            return await answer("pregunta", client, model, "fake", "fraud", show=lambda _: None)

    return asyncio.run(go(client or Client(create_server(verifier=None))))


def observations(model: ScriptedModel) -> list[dict]:
    return [json.loads(message["content"]) for message in model.received[-1] if message["role"] == "tool"]


def test_query_runs_and_its_result_goes_back_to_the_model():
    model = ScriptedModel(wants("get_transactions", customer_id="CUS-1001", limit=2), says("Cargo duplicado."))
    assert run(model) == "Cargo duplicado."
    first, second = observations(model)[0]["result"]
    assert first["amount"] == second["amount"]


def test_sensitive_action_is_not_executed():
    server = create_server(verifier=None)
    model = ScriptedModel(wants("block_card", card_id="CRD-2001", reason="robo"), says("Pendiente."))
    run(model, Client(server))
    assert observations(model)[0]["status"] == "pendiente_aprobacion"

    async def status() -> str:
        async with Client(server) as client:
            return (await client.call_tool("get_cards", {"customer_id": "CUS-1001"})).structured_content["result"][0]["status"]

    assert asyncio.run(status()) == "active"


def test_tool_error_reaches_the_model():
    model = ScriptedModel(wants("get_cards", customer_id="CUS-9999"), says("No existe."))
    run(model)
    assert "CUS-9999 no existe" in observations(model)[0]["error"]


def test_loop_stops_after_max_turns():
    model = ScriptedModel(wants("get_cards", customer_id="CUS-1001"))
    assert "No pude resolverlo" in run(model)
    assert len(model.received) == MAX_TURNS
