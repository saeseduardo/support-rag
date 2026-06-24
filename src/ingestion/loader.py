import re
from pathlib import Path
import pdfplumber


def load_document(path: Path) -> str:
    """Lee un PDF o archivo Markdown y devuelve texto limpio."""
    if path.suffix.lower() == ".pdf":
        raw = _load_pdf(path)
    elif path.suffix.lower() in (".md", ".txt"):
        raw = path.read_text(encoding="utf-8")
    else:
        raise ValueError(f"Formato no soportado: {path.suffix}")

    return clean_text(raw)


def _load_pdf(path: Path) -> str:
    """Extrae texto de todas las paginas de un PDF."""
    pages = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
    return "\n".join(pages)


def clean_text(text: str) -> str:
    """
    Limpia el texto antes de chunkear:
    - Quita lineas cortas (numeros de pagina, headers repetidos)
    - Quita caracteres de control
    - Normaliza espacios y saltos de linea
    """
    lines = text.splitlines()

    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        # Salta lineas muy cortas (tipicamente numeros de pagina o headers)
        if len(stripped) < 10:
            continue
        # Salta lineas que son solo numeros
        if stripped.isdigit():
            continue
        cleaned_lines.append(stripped)

    text = " ".join(cleaned_lines)

    # Quita caracteres de control excepto newlines
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # Normaliza espacios multiples
    text = re.sub(r" {2,}", " ", text)

    return text.strip()


def load_all_docs(docs_path: str = "./docs") -> list[dict]:
    """
    Carga todos los documentos de una carpeta.
    Devuelve lista de dicts con path y contenido limpio.
    """
    docs_dir = Path(docs_path)
    supported = {".pdf", ".md", ".txt"}
    results = []

    for file_path in sorted(docs_dir.rglob("*")):
        if file_path.suffix.lower() not in supported:
            continue
        try:
            content = load_document(file_path)
            if len(content) > 100:  # descarta archivos casi vacios
                results.append({
                    "path": str(file_path),
                    "name": file_path.name,
                    "content": content,
                })
        except Exception as e:
            print(f"Error leyendo {file_path}: {e}")

    return results
