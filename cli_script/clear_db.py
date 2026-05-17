import sys
import os
from pymongo import MongoClient

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import MONGODB_URI, MONGODB_DB_NAME

def clear_database():
    print(f"Connecting to MongoDB at {MONGODB_DB_NAME}...")
    client = MongoClient(MONGODB_URI)
    db = client[MONGODB_DB_NAME]
    
    # Collections used by LangGraph MongoDBSaver and MongoDBStore
    collections_to_clear = [
        "checkpoints", 
        "checkpoint_blobs", 
        "checkpoint_writes",
        "memories" # This is the custom namespace we used in the Store
    ]
    
    # Also clear users if we want a complete wipe, but usually we just want to clear memory
    # We will leave 'users' collection untouched by default unless specified
    
    print("\nStarting database cleanup...")
    for coll_name in collections_to_clear:
        if coll_name in db.list_collection_names():
            result = db[coll_name].delete_many({})
            print(f"✅ Cleared {result.deleted_count} documents from '{coll_name}'.")
        else:
            print(f"⏭️ Collection '{coll_name}' does not exist, skipping.")
            
    print("\nDatabase memory successfully cleared!")

if __name__ == "__main__":
    confirm = input("⚠️ Are you sure you want to delete ALL AI memory and audit logs? (y/N): ")
    if confirm.lower() == 'y':
        clear_database()
    else:
        print("Cleanup aborted.")
