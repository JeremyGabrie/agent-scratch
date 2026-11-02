"""Tool calling con las tools del MCP: el modelo de Foundry decide qué tool llamar, el código la ejecuta (ciclo ReAct).

Uso:
  uv run python dev/mcp/tool_calling.py "Soy CUS-1001, me cobraron dos veces en el supermercado"

Usa Foundry real (FOUNDRY_*, el mock de Foundry no hace tool calling) y el MCP del .env (MCP_*).
Las acciones sensibles no se ejecutan: el modelo recibe "pendiente de aprobación". La aprobación humana llega en la S8.
"""

import asyncio
import json
import sys
from collections.abc import Callable

from fastmcp import Client
from fastmcp.exceptions import ToolError
from mcp.types import Tool
from openai import OpenAI

from agent.infrastructure.config.settings import Settings
from agent.infrastructure.llm.credentials import build_credential
from agent.infrastructure.mcp.auth import mcp_bearer

MAX_TURNS = 5  # criterio de terminación: sin esto, un modelo confundido llama tools para siempre
SYSTEM = (
    "Eres el asistente del banco para el dominio {domain}. Responde en español, breve. "
    "Usa las tools para obtener los datos del cliente: nunca inventes montos, fechas ni estados. "
    "Si ninguna tool sirve para lo que piden, dilo. "
    "Las acciones sensibles quedan pendientes de aprobación de un asesor: díselo al cliente."
)


def as_function(tool: Tool) -> dict:
    """Una tool de MCP en el formato de tools de Foundry: nombre, descripción y el JSON Schema de sus parámetros."""
    return {"type": "function",
            "function": {"name": tool.name, "description": tool.description or "", "parameters": tool.input_schema}}


def is_sensitive(tool: Tool) -> bool:
    return bool(tool.annotations and tool.annotations.destructive_hint)


async def execute(client: Client, tool: Tool | None, name: str, arguments: dict) -> str:
    """Lo que vuelve al modelo como resultado de la tool. Siempre texto: un error también es información para él."""
    if tool is None:
        return json.dumps({"error": f"La tool {name} no existe."}, ensure_ascii=False)
    if is_sensitive(tool):
        return json.dumps({"status": "pendiente_aprobacion",
                           "detail": "Acción sensible: requiere aprobación humana, no se ejecutó."}, ensure_ascii=False)
    try:
        result = await client.call_tool(name, arguments)
    except ToolError as error:
        return json.dumps({"error": str(error)}, ensure_ascii=False)
    return json.dumps(result.structured_content, ensure_ascii=False)


async def answer(question: str, client: Client, model: OpenAI, deployment: str, domain: str,
                 show: Callable[[str], None] = print) -> str:
    tools = {tool.name: tool for tool in await client.list_tools()}  # solo las de tu dominio: las filtra el token
    functions = [as_function(tool) for tool in tools.values()]
    messages: list[dict] = [{"role": "system", "content": SYSTEM.format(domain=domain)},
                            {"role": "user", "content": question}]
    prompt_tokens = completion_tokens = 0
    for turn in range(1, MAX_TURNS + 1):
        completion = model.chat.completions.create(model=deployment, messages=messages, tools=functions)
        if completion.usage:
            prompt_tokens += completion.usage.prompt_tokens
            completion_tokens += completion.usage.completion_tokens
        message = completion.choices[0].message
        if not message.tool_calls:  # Thought → Answer: el modelo ya no pide nada
            show(f"[{turn}] respuesta final:\n    {message.content}")
            show(f"\n{turn} vueltas · {prompt_tokens} tokens de entrada · {completion_tokens} de salida")
            return message.content or ""
        messages.append({"role": "assistant", "content": message.content,
                         "tool_calls": [call.model_dump() for call in message.tool_calls]})
        for call in message.tool_calls:  # Action → Observation
            name, arguments = call.function.name, json.loads(call.function.arguments or "{}")
            tool = tools.get(name)
            shown = ", ".join(f"{key}={value!r}" for key, value in arguments.items())
            show(f"[{turn}] el modelo pide: {name}({shown})")
            observation = await execute(client, tool, name, arguments)
            label = "NO SE EJECUTA" if tool and is_sensitive(tool) else "resultado"
            show(f"    {label}: {observation[:200]}")
            messages.append({"role": "tool", "tool_call_id": call.id, "content": observation})
    show(f"Se cortó en {MAX_TURNS} vueltas sin respuesta final.")
    return f"No pude resolverlo en {MAX_TURNS} pasos. Un asesor te contactará."


async def main(question: str) -> int:
    settings = Settings()
    foundry = settings.foundry
    model = OpenAI(base_url=f"{foundry.endpoint.rstrip('/')}/openai/v1/",
                   api_key=build_credential(foundry.auth_provider, foundry.api_key), timeout=foundry.timeout_s)
    async with Client(settings.mcp.url, auth=mcp_bearer(settings.mcp)) as client:
        await answer(question, client, model, foundry.deployment, settings.domain)
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    sys.exit(asyncio.run(main(sys.argv[1])))
