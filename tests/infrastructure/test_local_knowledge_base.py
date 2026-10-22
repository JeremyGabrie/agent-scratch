from agent.domain.knowledge import Chunk
from agent.infrastructure.search.local_knowledge_base import LocalKnowledgeBase, read_chunks


def chunk(id_: str, fuente: str) -> Chunk:
    return Chunk(id=id_, content="texto", doc_type="faq", seccion="FAQ", fuente=fuente)


def test_publish_replaces_the_chunks_of_each_source(tmp_path):
    index = LocalKnowledgeBase(tmp_path / "index.json")
    index.publish([chunk("a1", "a.md"), chunk("a2", "a.md"), chunk("b1", "b.md")])

    index.publish([chunk("a3", "a.md")])

    assert sorted(c.id for c in read_chunks(tmp_path / "index.json")) == ["a3", "b1"]
    assert index.count() == 2
