from agent.domain.knowledge import Citation, SearchHit
from agent.domain.models import AgentTurn, Message, Usage
from agent.domain.ports import ChatModel, ConversationStore, Embedder, KnowledgeBase, QueryRewriter

REWRITE_PROMPT = (
    "Reescribe la última pregunta del cliente para que se entienda sola, sin leer la conversación. "
    "Conserva los productos, montos y fechas que se mencionaron antes. No la respondas."
)
CONTEXT_HEADER = (
    "Fragmentos del corpus para la última pregunta. Si es consulta_producto, responde solo con ellos y pon en "
    "fuentes los números que usaste; si no tienen la respuesta, dilo. No escribas los números dentro de la respuesta."
)


class ChatService:
    """Caso de uso: resolver un turno de conversación con RAG. Solo conoce puertos, nunca infraestructura."""

    def __init__(
        self,
        model: ChatModel,
        rewriter: QueryRewriter,
        embedder: Embedder,
        knowledge_base: KnowledgeBase,
        store: ConversationStore,
        system_prompt: str,
        max_turns: int,
        top_k: int,
    ) -> None:
        self.model = model
        self.rewriter = rewriter
        self.embedder = embedder
        self.knowledge_base = knowledge_base
        self.store = store
        self.system_prompt = system_prompt
        self.max_turns = max_turns
        self.top_k = top_k

    def handle(self, session_id: str, message: str) -> AgentTurn:
        user: Message = {"role": "user", "content": message}
        recent = self.store.get(session_id)[-self.max_turns * 2 :]

        query, usage = message, Usage()
        if recent:  # la primera pregunta ya se entiende sola: no se gasta una llamada en reescribirla
            rewritten = self.rewriter.rewrite([{"role": "system", "content": REWRITE_PROMPT}, *recent, user])
            query, usage = rewritten.query, rewritten.usage
        hits = self.knowledge_base.search(query, self.embedder.embed([query])[0], self.top_k)

        context: Message = {"role": "system", "content": _context_message(hits)}
        result = self.model.complete([{"role": "system", "content": self.system_prompt}, *recent, context, user])
        # se guarda solo si el modelo respondió: un error no deja turnos a medias. El contexto no se guarda:
        # cada turno busca de nuevo, y el historial no crece con fragmentos viejos
        self.store.append(session_id, user)
        self.store.append(session_id, {"role": "assistant", "content": result.reply.answer})
        return AgentTurn(
            reply=result.reply, usage=usage + result.usage, citations=_citations_from(result.reply.fuentes, hits)
        )


def _context_message(hits: list[SearchHit]) -> str:
    if not hits:
        return "No se encontraron fragmentos del corpus para esta pregunta."
    blocks = [f"[{number}] {hit.chunk.fuente}\n{hit.chunk.content}" for number, hit in enumerate(hits, start=1)]
    return "\n\n".join([CONTEXT_HEADER, *blocks])


def _citations_from(numbers: list[int], hits: list[SearchHit]) -> list[Citation]:
    # el modelo solo elige números; uno que no existe se descarta, así ninguna cita es inventada
    cited_chunks = [hits[number - 1].chunk for number in dict.fromkeys(numbers) if 1 <= number <= len(hits)]
    return [Citation(fuente=chunk.fuente, seccion=chunk.seccion, chunk_id=chunk.id) for chunk in cited_chunks]
