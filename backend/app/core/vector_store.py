# from pathlib import Path

# from langchain_community.vectorstores import Chroma
# from langchain_core.documents import Document
# # from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from app.config import settings

# from langchain_mistralai import MistralAIEmbeddings


# _embeddings = None


# def get_embeddings():
#     global _embeddings

#     if _embeddings is None:

#         print("Initializing Mistral Embeddings...")

#         _embeddings = MistralAIEmbeddings(
#             model="mistral-embed",
#             api_key=settings.MISTRAL_API_KEY,
#         )

#     return _embeddings


# def build_vector_store(
#     meeting_id: str,
#     transcript: str,
# ) -> Chroma:

#     splitter = RecursiveCharacterTextSplitter(
#         chunk_size=500,
#         chunk_overlap=50,
#     )

#     chunks = splitter.split_text(transcript)

#     docs = [
#         Document(
#             page_content=chunk,
#             metadata={"chunk_index": i},
#         )
#         for i, chunk in enumerate(chunks)
#     ]

#     persist_dir = Path(settings.VECTOR_DB_DIR) / meeting_id

#     persist_dir.mkdir(parents=True, exist_ok=True)

#     vector_store = Chroma.from_documents(
#         documents=docs,
#         embedding=get_embeddings(),
#         collection_name=meeting_id,
#         persist_directory=str(persist_dir),
#     )

#     return vector_store


# def load_vector_store(meeting_id: str):

#     persist_dir = Path(settings.VECTOR_DB_DIR) / meeting_id

#     return Chroma(
#         collection_name=meeting_id,
#         embedding_function=get_embeddings(),
#         persist_directory=str(persist_dir),
#     )


# def get_retriever(
#     vector_store: Chroma,
#     k: int = 4,
# ):

#     return vector_store.as_retriever(
#         search_type="similarity",
#         search_kwargs={"k": k},
#     )

from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_mistralai import MistralAIEmbeddings

from app.config import settings

_embeddings = None


# ==========================================================
# Embeddings (Singleton)
# ==========================================================

def get_embeddings():

    global _embeddings

    if _embeddings is None:

        print("Initializing Mistral Embeddings...")

        _embeddings = MistralAIEmbeddings(
            model="mistral-embed",
            api_key=settings.MISTRAL_API_KEY,
        )

    return _embeddings


# ==========================================================
# Build Vector Store
# ==========================================================

def build_vector_store(
    meeting_id: str,
    transcript: str,
) -> Chroma:

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )

    chunks = splitter.split_text(transcript)

    persist_dir = Path(settings.VECTOR_DB_DIR) / meeting_id
    persist_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    vector_store = Chroma(
        collection_name=meeting_id,
        embedding_function=get_embeddings(),
        persist_directory=str(persist_dir),
    )

    BATCH_SIZE = settings.VECTOR_BATCH_SIZE

    total = len(chunks)

    print(f"Building Vector Store ({total} chunks)...")

    for start in range(0, total, BATCH_SIZE):

        end = min(start + BATCH_SIZE, total)

        docs = [

            Document(
                page_content=chunk,
                metadata={
                    "chunk_index": start + i,
                },
            )

            for i, chunk in enumerate(chunks[start:end])

        ]

        vector_store.add_documents(docs)

        print(f"Embedded {end}/{total} chunks")

    print("Vector Store Complete.")

    return vector_store


# ==========================================================
# Load Existing Vector Store
# ==========================================================

def load_vector_store(
    meeting_id: str,
):

    persist_dir = Path(settings.VECTOR_DB_DIR) / meeting_id

    return Chroma(
        collection_name=meeting_id,
        embedding_function=get_embeddings(),
        persist_directory=str(persist_dir),
    )


# ==========================================================
# Retriever
# ==========================================================

def get_retriever(
    vector_store: Chroma,
    k: int = 4,
):

    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": k,
        },
    )