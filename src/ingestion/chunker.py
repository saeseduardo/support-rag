from langchain.text_splitter import RecursiveCharacterTextSplitter
from src.config import settings

# Separadores en orden de preferencia:
# primero intenta cortar en parrafos, luego oraciones, luego palabras
_splitter = RecursiveCharacterTextSplitter(
    chunk_size=settings.chunk_size,       # 512 tokens por defecto
    chunk_overlap=settings.chunk_overlap,  # 50 tokens de overlap
    separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
    length_function=len,
)


def chunk_document(content: str, source_file: str) -> list[dict]:
    """
    Divide el contenido en chunks y agrega metadata.
    Devuelve lista de dicts listos para embeddear y guardar.
    """
    raw_chunks = _splitter.split_text(content)

    chunks = []
    for i, chunk_text in enumerate(raw_chunks):
        chunk_text = chunk_text.strip()
        if len(chunk_text) < 20:  # descarta chunks triviales
            continue
        chunks.append({
            "content": chunk_text,
            "source_file": source_file,
            "chunk_index": i,
            "metadata": {
                "char_count": len(chunk_text),
                "word_count": len(chunk_text.split()),
            },
        })

    return chunks
