from agent.application.chunker import chunk_document
from agent.domain.knowledge import SourceDocument


def doc(markdown: str, fuente: str = "doc.md") -> SourceDocument:
    return SourceDocument(fuente=fuente, doc_type="reglamento", markdown=markdown)


REGLAMENTO = """# Reglamento

## 4. Plazos de respuesta

El banco responde en 15 días hábiles.

### 4.1 Ampliación del plazo

Puede ampliarse una vez por 15 días hábiles.
"""


def test_chunks_keep_their_heading_path():
    chunks = chunk_document(doc(REGLAMENTO), max_chars=500)

    assert [c.seccion for c in chunks] == [
        "Reglamento > 4. Plazos de respuesta",
        "Reglamento > 4. Plazos de respuesta > 4.1 Ampliación del plazo",
    ]
    assert chunks[1].content.startswith("Reglamento > 4. Plazos de respuesta > 4.1 Ampliación del plazo\n\n")
    assert all(c.fuente == "doc.md" and c.doc_type == "reglamento" for c in chunks)


def test_long_section_is_split_under_max_chars():
    body = "\n\n".join(f"Párrafo {i}. " + "texto " * 30 for i in range(10))
    chunks = chunk_document(doc(f"# Guía\n\n{body}"), max_chars=400)

    assert len(chunks) > 1
    assert all(len(c.content) <= 400 + len("Guía\n\n") for c in chunks)


def test_table_chunks_repeat_the_header():
    rows = "\n".join(f"| tipo_{i} | {i} |" for i in range(40))
    chunks = chunk_document(doc(f"# plazos\n\n| tipo | dias |\n| --- | --- |\n{rows}"), max_chars=200)

    assert len(chunks) > 1
    assert all("| tipo | dias |\n| --- | --- |" in c.content for c in chunks)


def test_ids_are_stable_and_unique():
    first = chunk_document(doc(REGLAMENTO), max_chars=500)
    again = chunk_document(doc(REGLAMENTO), max_chars=500)
    other = chunk_document(doc(REGLAMENTO, fuente="otro.md"), max_chars=500)

    assert [c.id for c in first] == [c.id for c in again]
    assert len({c.id for c in first + other}) == len(first) + len(other)


def test_headings_without_text_produce_no_chunks():
    assert chunk_document(doc("# Título\n\n## Vacía\n\n## También vacía\n"), max_chars=500) == []
