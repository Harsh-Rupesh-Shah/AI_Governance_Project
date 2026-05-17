"""
ChromaDB Inspector
══════════════════
A simple utility to peek inside our vector database
and see the indexed policy chunks.
"""

import sys
import os
import io

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.vectordb import get_vector_store

def inspect():
    print("\n" + "="*50)
    print("      CHROMADB INSPECTION")
    print("="*50)
    
    try:
        vector_store = get_vector_store()
        collection = vector_store._collection
        
        count = collection.count()
        print(f"\n[SUMMARY]")
        print(f"  Collection Name: {collection.name}")
        print(f"  Total Chunks:    {count}")
        
        if count > 0:
            print(f"\n[SAMPLE CHUNKS (Top 3)]")
            results = collection.peek(limit=3)
            
            for i in range(len(results['documents'])):
                doc = results['documents'][i]
                metadata = results['metadatas'][i]
                print(f"\n  CHUNK #{i+1}")
                print(f"  Source: {metadata.get('source', 'unknown')}")
                print(f"  Content snippet: {doc[:150].replace('\n', ' ')}...")
                print("-" * 30)
        else:
            print("\n  The database is currently empty.")
            
    except Exception as e:
        print(f"\n[ERROR] Could not inspect database: {str(e)}")
        
    print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    inspect()
