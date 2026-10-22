import json
from pathlib import Path

from pydantic import TypeAdapter

from agent.domain.knowledge import Chunk

_CHUNKS = TypeAdapter(list[Chunk])


def read_chunks(path: Path) -> list[Chunk]:
    return _CHUNKS.validate_json(path.read_bytes()) if path.is_file() else []


def write_chunks(path: Path, chunks: list[Chunk]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_CHUNKS.dump_python(chunks, mode="json"), ensure_ascii=False, indent=1), encoding="utf-8")


class LocalKnowledgeBase:
    """Implementa KnowledgeBase en un archivo JSON: desarrollo sin Azure y baseline frente a AI Search."""

    # ponytail: carga el archivo completo en cada operación; alcanza para miles de chunks por dominio
    def __init__(self, path: Path) -> None:
        self.path = path

    def publish(self, chunks: list[Chunk]) -> None:
        fuentes = {c.fuente for c in chunks}
        kept = [c for c in read_chunks(self.path) if c.fuente not in fuentes]
        write_chunks(self.path, kept + chunks)

    def count(self) -> int:
        return len(read_chunks(self.path))
