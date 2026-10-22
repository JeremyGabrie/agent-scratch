"""Chunking por secciones de Markdown: cada chunk sabe de qué sección viene."""

import re
import uuid

from agent.domain.knowledge import Chunk, SourceDocument

HEADING = re.compile(r"^(#{1,6})\s+(.+)$")


def chunk_document(doc: SourceDocument, max_chars: int) -> list[Chunk]:
    chunks = []
    for path, body in _sections(doc.markdown):
        seccion = " > ".join(path)
        for n, piece in enumerate(_split(body, max_chars)):
            chunks.append(
                Chunk(
                    id=_chunk_id(doc.fuente, seccion, n),
                    # el camino de títulos va dentro del texto: da contexto al embedding y a la búsqueda por palabras
                    content=f"{seccion}\n\n{piece}",
                    doc_type=doc.doc_type,
                    producto=doc.producto,
                    seccion=seccion,
                    vigencia_desde=doc.vigencia_desde,
                    vigencia_hasta=doc.vigencia_hasta,
                    fuente=doc.fuente,
                )
            )
    return chunks


def _sections(markdown: str) -> list[tuple[list[str], str]]:
    """Agrupa el texto bajo su camino de títulos, por ejemplo [Reglamento, 4. Plazos, 4.1 Ampliación]."""
    sections, path, body = [], [], []
    for line in markdown.splitlines():
        if m := HEADING.match(line):
            if text := "\n".join(body).strip():
                sections.append((list(path), text))
            level = len(m[1])
            path = path[: level - 1] + [m[2].strip()]
            body = []
        else:
            body.append(line)
    if text := "\n".join(body).strip():
        sections.append((list(path), text))
    return sections


def _split(body: str, max_chars: int) -> list[str]:
    if body.startswith("|"):
        return _split_table(body.splitlines(), max_chars)
    # ponytail: empaqueta párrafos hasta max_chars; un párrafo más largo se corta por oraciones
    pieces, current = [], ""
    for para in _units(body, max_chars):
        if current and len(current) + len(para) + 2 > max_chars:
            pieces.append(current)
            current = para
        else:
            current = f"{current}\n\n{para}" if current else para
    return pieces + [current] if current else pieces


def _units(body: str, max_chars: int) -> list[str]:
    units = []
    for para in (p.strip() for p in re.split(r"\n\s*\n", body)):
        if len(para) <= max_chars:
            units.append(para)
        else:
            units += [s for s in re.split(r"(?<=[.;:])\s+", para) if s]
    return [u for u in units if u]


def _split_table(lines: list[str], max_chars: int) -> list[str]:
    """Tablas: cada chunk repite el encabezado, así una fila suelta conserva el nombre de sus columnas."""
    header, rows = lines[:2], lines[2:]
    pieces, current = [], []
    for row in rows:
        if current and len("\n".join(header + current + [row])) > max_chars:
            pieces.append("\n".join(header + current))
            current = []
        current.append(row)
    return pieces + ["\n".join(header + current)] if current else pieces


def _chunk_id(fuente: str, seccion: str, n: int) -> str:
    # determinístico: reindexar el mismo documento reemplaza sus chunks en vez de duplicarlos.
    # UUID porque Qdrant (y otras bases vectoriales) solo aceptan números o UUID como id
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{fuente}|{seccion}|{n}"))
