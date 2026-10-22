from datetime import date

from pydantic import BaseModel


class SourceDocument(BaseModel):
    """Documento del corpus convertido a Markdown, con la metadata de su manifest."""

    fuente: str
    doc_type: str
    producto: str | None = None
    vigencia_desde: date | None = None
    vigencia_hasta: date | None = None
    markdown: str


class Chunk(BaseModel):
    """Unidad que se indexa. Es el mismo esquema que idx-team-NN en Azure AI Search."""

    id: str
    content: str
    content_vector: list[float] = []
    doc_type: str
    producto: str | None = None
    seccion: str
    vigencia_desde: date | None = None
    vigencia_hasta: date | None = None
    fuente: str
