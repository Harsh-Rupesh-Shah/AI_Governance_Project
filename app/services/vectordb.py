"""
Vector Database Service
═══════════════════════
Initializes ChromaDB and handles the ingestion and retrieval
of policy documents using Google Generative AI embeddings.
"""

import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
import chromadb
from langchain_huggingface import HuggingFaceEmbeddings

from app.config import GOOGLE_API_KEY

# Configure the embeddings model using a local HuggingFace model
# This completely bypasses the Gemini API rate limits!
embeddings = HuggingFaceEmbeddings(
    model_name="all-MiniLM-L6-v2"
)

CHROMA_PERSIST_DIR = "./data/chroma"
COLLECTION_NAME = "governance_policies"

def get_vector_store():
    """Returns the Chroma vector store instance using PersistentClient."""
    persistent_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    return Chroma(
        client=persistent_client,
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
    )

def ingest_policies():
    """
    Loads policy documents from the app/policies directory,
    splits them into chunks, and stores them in ChromaDB.
    Should be run once or whenever policies are updated.
    """
    policy_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "policies")
    
    documents = []
    # Load all markdown and text files from the policies directory
    for filename in os.listdir(policy_dir):
        if filename.endswith(".md") or filename.endswith(".txt"):
            file_path = os.path.join(policy_dir, filename)
            loader = TextLoader(file_path, encoding='utf-8')
            documents.extend(loader.load())

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
        persistent_client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass # Collection might not exist yet
    
    vector_store = Chroma(
        client=persistent_client,
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
    )
    
    # Add documents explicitly in one go
    # Since we are using local HuggingFace embeddings, there are no rate limits!
    vector_store.add_documents(documents=chunks)
    
    print(f"Successfully ingested {len(chunks)} policy chunks into ChromaDB.")

def retrieve_relevant_policies(query: str, top_k: int = 3):
    """
    Retrieves the top_k most relevant policy chunks for a given query.
    """
    vector_store = get_vector_store()
    results = vector_store.similarity_search(query, k=top_k)
    return [doc.page_content for doc in results]

if __name__ == "__main__":
    # If run directly, ingest the policies
    print("Ingesting policies...")
    ingest_policies()
