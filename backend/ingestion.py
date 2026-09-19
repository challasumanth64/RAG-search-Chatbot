import os
import tempfile
from typing import TYPE_CHECKING, List, Tuple
from fastapi import UploadFile

from langchain_core.documents import Document

if TYPE_CHECKING:
    from langchain_community.vectorstores import Chroma

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")
EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"

# Global lazy placeholder
_embeddings = None

def get_embeddings():
    """Loads HuggingFace BGE embeddings lazily on first call."""
    global _embeddings
    if _embeddings is None:
        from langchain_huggingface import HuggingFaceEmbeddings
        _embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    return _embeddings

def get_vectorstore() -> "Chroma":
    """Returns persistent ChromaDB instance."""
    from langchain_community.vectorstores import Chroma

    return Chroma(
        persist_directory=CHROMA_PATH,
        embedding_function=get_embeddings(),
        collection_name="rag_collection"
    )

def parse_document(file: UploadFile) -> List[Document]:
    """Saves uploaded file to temp path and parses text content with metadata."""
    from langchain_community.document_loaders import (
        Docx2txtLoader,
        PyPDFLoader,
        TextLoader,
    )

    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
        temp_file.write(file.file.read())
        temp_path = temp_file.name

    try:
        if ext == ".pdf":
            loader = PyPDFLoader(temp_path)
            docs = loader.load()
            for i, doc in enumerate(docs):
                doc.metadata["source"] = filename
                doc.metadata["page"] = doc.metadata.get("page", i) + 1
                doc.metadata["type"] = "pdf"
        elif ext == ".docx":
            loader = Docx2txtLoader(temp_path)
            docs = loader.load()
            for doc in docs:
                doc.metadata["source"] = filename
                doc.metadata["page"] = 1
                doc.metadata["type"] = "docx"
        elif ext in [".txt", ".md"]:
            loader = TextLoader(temp_path, encoding="utf-8")
            docs = loader.load()
            for doc in docs:
                doc.metadata["source"] = filename
                doc.metadata["page"] = 1
                doc.metadata["type"] = ext[1:]
        else:
            raise ValueError(f"Unsupported file format: {ext}")
        return docs
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

def process_and_index_file(file: UploadFile) -> Tuple[int, str]:
    """Ingests document into ChromaDB persistent storage."""
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    docs = parse_document(file)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=150,
        length_function=len
    )
    chunks = splitter.split_documents(docs)

    vectorstore = get_vectorstore()
    vectorstore.add_documents(chunks)

    return len(chunks), file.filename