"""Convierte cada formato del corpus a Markdown con títulos (#, ##, ###), que es lo que entiende el chunker."""

import csv
import io
import json
import re
from html.parser import HTMLParser
from pathlib import Path

from docx import Document
from pypdf import PdfReader

from agent.domain.knowledge import SourceDocument

# "1. Objeto" o "3.1 Plazo": número de sección seguido de un título con mayúscula
PDF_HEADING = re.compile(r"^(\d+)\.(\d+)?\s+[A-ZÁÉÍÓÚÑ¿]")


def load_corpus(corpus_dir: Path) -> list[SourceDocument]:
    manifest = json.loads((corpus_dir / "manifest.json").read_text(encoding="utf-8"))
    return [SourceDocument(markdown=to_markdown(corpus_dir / entry["fuente"]), **entry) for entry in manifest]


def to_markdown(path: Path) -> str:
    match path.suffix.lower():
        case ".md":
            return path.read_text(encoding="utf-8")
        case ".csv":
            return csv_to_markdown(path.stem, path.read_text(encoding="utf-8"))
        case ".html":
            return html_to_markdown(path.read_text(encoding="utf-8"))
        case ".docx":
            return docx_to_markdown(path)
        case ".pdf":
            return pdf_text_to_markdown("\n".join(page.extract_text() or "" for page in PdfReader(path).pages))
        case other:
            raise ValueError(f"formato no soportado: {other} ({path.name})")


def csv_to_markdown(title: str, text: str) -> str:
    rows = list(csv.reader(io.StringIO(text)))
    lines = [f"# {title}", "", _md_row(rows[0]), _md_row(["---"] * len(rows[0]))]
    return "\n".join(lines + [_md_row(r) for r in rows[1:]]) + "\n"


def _md_row(cells: list[str]) -> str:
    return "| " + " | ".join(c.strip() for c in cells) + " |"


class _HtmlToMarkdown(HTMLParser):
    SKIP = {"nav", "footer", "script", "style", "head"}

    def __init__(self) -> None:
        super().__init__()
        self.lines: list[str] = []
        self.prefix = ""
        self.skip_depth = 0
        self.text: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in self.SKIP:
            self.skip_depth += 1
        elif re.fullmatch(r"h[1-6]", tag):
            self.prefix = "#" * int(tag[1]) + " "
        elif tag == "li":
            self.prefix = "- "

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP:
            self.skip_depth -= 1
        elif tag in {"h1", "h2", "h3", "h4", "h5", "h6", "p", "li"}:
            if text := " ".join("".join(self.text).split()):
                self.lines += [self.prefix + text, ""] if tag != "li" else [self.prefix + text]
            self.text, self.prefix = [], ""
        elif tag == "ul":
            self.lines.append("")

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            self.text.append(data)


def html_to_markdown(html: str) -> str:
    parser = _HtmlToMarkdown()
    parser.feed(html)
    return "\n".join(parser.lines)


def docx_to_markdown(path: Path) -> str:
    lines = []
    for para in Document(path).paragraphs:
        text, style = para.text.strip(), para.style.name
        if not text:
            continue
        if style == "Title":
            lines += [f"# {text}", ""]
        elif style.startswith("Heading "):
            lines += ["#" * (int(style.split()[1]) + 1) + f" {text}", ""]
        elif style.startswith("List"):
            lines.append(f"- {text}")
        else:
            lines += [text, ""]
    return "\n".join(lines)


def pdf_text_to_markdown(text: str) -> str:
    """El PDF no trae estilos: la primera línea es el título y las secciones se reconocen por su numeración."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return ""
    out, paragraph = [f"# {lines[0]}", ""], []
    for line in lines[1:]:
        if m := PDF_HEADING.match(line):
            if paragraph:
                out += [" ".join(paragraph), ""]
                paragraph = []
            out += [("###" if m[2] else "##") + f" {line}", ""]
        else:
            paragraph.append(line)
    if paragraph:
        out.append(" ".join(paragraph))
    return "\n".join(out)
