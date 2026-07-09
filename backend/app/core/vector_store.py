from pathlib import Path

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings

_embeddings = None


def get_embeddings():
    global _embeddings

    if _embeddings is None:

        print("Loading embedding model...")

        _embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
        )

    return _embeddings


def build_vector_store(
    meeting_id: str,
    transcript: str,
) -> Chroma:

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )

    chunks = splitter.split_text(transcript)

    docs = [
        Document(
            page_content=chunk,
            metadata={"chunk_index": i},
        )
        for i, chunk in enumerate(chunks)
    ]

    persist_dir = Path(settings.VECTOR_DB_DIR) / meeting_id

    persist_dir.mkdir(parents=True, exist_ok=True)

    vector_store = Chroma.from_documents(
        documents=docs,
        embedding=get_embeddings(),
        collection_name=meeting_id,
        persist_directory=str(persist_dir),
    )

    return vector_store


def load_vector_store(meeting_id: str):

    persist_dir = Path(settings.VECTOR_DB_DIR) / meeting_id

    return Chroma(
        collection_name=meeting_id,
        embedding_function=get_embeddings(),
        persist_directory=str(persist_dir),
    )


def get_retriever(
    vector_store: Chroma,
    k: int = 4,
):

    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k},
    )