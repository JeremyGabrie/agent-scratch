from datetime import date

from agent.domain.knowledge import Chunk
from agent.infrastructure.search.azure_search_knowledge_base import from_document, still_valid_filter, to_document


def test_documents_use_the_date_format_of_the_index():
    chunk = Chunk(id="c1", content="x", content_vector=[0.1], doc_type="faq", seccion="FAQ", fuente="a.md",
                  vigencia_hasta=date(2024, 12, 31))

    document = to_document(chunk)

    assert document["vigencia_hasta"] == "2024-12-31T00:00:00Z"
    assert document["vigencia_desde"] is None
    assert from_document({**document, "@search.score": 1.0}) == chunk.model_copy(update={"content_vector": []})
    assert still_valid_filter(date(2026, 10, 23)) == "vigencia_hasta eq null or vigencia_hasta ge 2026-10-23T00:00:00Z"
