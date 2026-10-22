import json
from datetime import date

from docx import Document

from agent.infrastructure.ingestion.loaders import (
    csv_to_markdown,
    html_to_markdown,
    load_corpus,
    pdf_text_to_markdown,
    to_markdown,
)


def test_csv_becomes_a_markdown_table():
    md = csv_to_markdown("plazos", "tipo,dias\nfraude,10\n")
    assert md == "# plazos\n\n| tipo | dias |\n| --- | --- |\n| fraude | 10 |\n"


def test_html_keeps_headings_and_lists_but_drops_navigation():
    html = "<nav>Inicio</nav><h1>Canales</h1><h2>App</h2><p>Disponible 24 horas.</p><ul><li>Bloqueo</li></ul><footer>pie</footer>"
    md = html_to_markdown(html)
    assert md.splitlines()[:6] == ["# Canales", "", "## App", "", "Disponible 24 horas.", ""]
    assert "- Bloqueo" in md
    assert "Inicio" not in md and "pie" not in md


def test_html_tables_become_markdown_tables():
    html = "<h2>Comisiones</h2><table><tr><th>Concepto</th><th>Monto</th></tr><tr><td>Retiro</td><td>S/ 7.50</td></tr></table>"
    assert html_to_markdown(html).splitlines()[:5] == [
        "## Comisiones", "", "| Concepto | Monto |", "| --- | --- |", "| Retiro | S/ 7.50 |",
    ]


def test_docx_tables_keep_their_place(tmp_path):
    path = tmp_path / "tarifario.docx"
    d = Document()
    d.add_heading("Servicios", level=1)
    table = d.add_table(rows=2, cols=2)
    for i, row in enumerate([["Servicio", "Comisión"], ["Carta", "S/ 25"]]):
        for j, text in enumerate(row):
            table.cell(i, j).text = text
    d.add_paragraph("Las constancias digitales no tienen costo.")
    d.save(path)

    assert to_markdown(path).splitlines()[:6] == [
        "## Servicios", "", "| Servicio | Comisión |", "| --- | --- |", "| Carta | S/ 25 |", "",
    ]
    assert "Las constancias digitales no tienen costo." in to_markdown(path)


def test_docx_headings_follow_the_same_levels(tmp_path):
    path = tmp_path / "politica.docx"
    d = Document()
    d.add_heading("Política", level=0)
    d.add_heading("Canales", level=1)
    d.add_paragraph("App y teléfono.")
    d.save(path)

    assert to_markdown(path).splitlines()[:5] == ["# Política", "", "## Canales", "", "App y teléfono."]


def test_pdf_sections_are_detected_by_numbering():
    text = "Reglamento\n1. Objeto\nEste reglamento aplica\na todos los canales.\n3.1 Plazo para presentar\nHasta 60 días.\n4111 1111 no es un título"
    md = pdf_text_to_markdown(text)
    assert md.splitlines() == [
        "# Reglamento", "",
        "## 1. Objeto", "",
        "Este reglamento aplica a todos los canales.", "",
        "### 3.1 Plazo para presentar", "",
        "Hasta 60 días. 4111 1111 no es un título",
    ]


def test_load_corpus_reads_the_manifest(tmp_path):
    (tmp_path / "faq.md").write_text("# FAQ\n\n## Pregunta\n\nRespuesta.\n", encoding="utf-8")
    manifest = [{"fuente": "faq.md", "doc_type": "faq", "producto": None, "vigencia_desde": "2025-01-01", "vigencia_hasta": None}]
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    [doc] = load_corpus(tmp_path)

    assert doc.fuente == "faq.md" and doc.vigencia_desde == date(2025, 1, 1)
    assert doc.markdown.startswith("# FAQ")
