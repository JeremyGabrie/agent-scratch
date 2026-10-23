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


class SearchHit(BaseModel):
    """Un chunk que encontró la búsqueda, con su puntaje: más alto, más relevante."""

    chunk: Chunk
    score: float


class Citation(BaseModel):
    """De dónde salió una respuesta: el documento y la sección del chunk que usó el modelo."""

    fuente: str
    seccion: str
    chunk_id: str
