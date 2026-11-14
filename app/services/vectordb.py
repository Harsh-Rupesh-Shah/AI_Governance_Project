"""
Vector Database Service
═══════════════════════
Initializes ChromaDB and handles the ingestion and retrieval
of policy documents using Google Generative AI embeddings.
"""

import sys
import logging
from pathlib import Path

# Ensure project root is in sys.path when running vectordb.py directly
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
import chromadb
from langchain_huggingface import HuggingFaceEmbeddings

from app.config import CHROMA_PERSIST_DIR, CHROMA_COLLECTION_NAME

logger = logging.getLogger(__name__)

# Configure the embeddings model using a local HuggingFace model (lazy loaded)
_embeddings = None

def get_embeddings():
    """Lazily load the HuggingFace embeddings model on first use."""
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )
    return _embeddings

def get_vector_store():
    """Returns the Chroma vector store instance using PersistentClient."""
    persistent_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    return Chroma(
        client=persistent_client,
        collection_name=CHROMA_COLLECTION_NAME,
        embedding_function=get_embeddings(),
    )

def ingest_policies():
    """
    Loads policy documents from the app/policies directory,
    splits them into chunks, and stores them in ChromaDB.
    Should be run once or whenever policies are updated.
    """
    policy_dir = Path(__file__).resolve().parent.parent / "policies"
    
    documents = []
    # Load all markdown and text files from the policies directory
    for file_path in policy_dir.glob("*"):
        if file_path.suffix in [".md", ".txt"]:
            content = file_path.read_text(encoding="utf-8")
            if content.strip():
                documents.append(
                    Document(
                        page_content=content,
                        metadata={"source": file_path.name}
                    )
                )

    if not documents:
        print("No policy documents found to ingest.")
        return

    # Split documents into smaller semantic chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""]
    )
    
    chunks = text_splitter.split_documents(documents)
    
    # Initialize PersistentClient
    persistent_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    
    # Clear existing collection if it exists to avoid duplicates
    try:
        persistent_client.delete_collection(CHROMA_COLLECTION_NAME)
    except Exception:
        pass # Collection might not exist yet
    
    vector_store = Chroma(
        client=persistent_client,
        collection_name=CHROMA_COLLECTION_NAME,
        embedding_function=get_embeddings(),
    )
    
    # Add documents explicitly in one go
    # Since we are using local HuggingFace embeddings, there are no rate limits!
    vector_store.add_documents(documents=chunks)
    
    print(f"Successfully ingested {len(chunks)} policy chunks into ChromaDB.")

def retrieve_relevant_policies(query: str, top_k: int = 3):
    """
    Retrieves the top_k most relevant policy chunks for a given query.
    Gracefully returns empty list if collection is empty or not yet indexed.
    """
    try:
        vector_store = get_vector_store()
        results = vector_store.similarity_search(query, k=top_k)
        return [doc.page_content for doc in results]
    except Exception as e:
        logger.warning(f"Could not retrieve policies from ChromaDB: {e}")
        return []

if __name__ == "__main__":
    # If run directly, ingest the policies
    print("Ingesting policies...")
    ingest_policies()
