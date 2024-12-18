import sys
import chromadb
from chromadb.config import Settings
import json

# Configure path - adjust this based on your setup
CHROMA_PATH = "../backend/data/vector_db"

def get_chroma_client():
    return chromadb.PersistentClient(
        path=CHROMA_PATH,
        settings=Settings(
            allow_reset=True,
            anonymized_telemetry=False
        )
    )

def get_collection_data(collection_name):
    client = get_chroma_client()
    try:
        collection = client.get_collection(name=collection_name)
        data = collection.get()
        return data
    except Exception as e:
        print(f"Error retrieving collection '{collection_name}': {str(e)}")
        return None

def print_collection_data(data):
    if data is None:
        return

    print("Collection Data:")
    print("=" * 50)

    print("\nIDs:")
    print(json.dumps(data['ids'], indent=2))

    print("\nEmbeddings:")
    if data['embeddings']:
        print(f"Number of embeddings: {len(data['embeddings'])}")
        print("First embedding:")
        print(json.dumps(data['embeddings'][0][:10] + ['...'], indent=2))
    else:
        print("No embeddings found.")

    print("\nMetadata:")
    print(json.dumps(data['metadatas'], indent=2))

    print("\nDocuments:")
    print(json.dumps(data['documents'], indent=2))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script_name.py <collection_name>")
        sys.exit(1)

    collection_name = sys.argv[1]
    collection_data = get_collection_data(collection_name)

    if collection_data:
        print_collection_data(collection_data)
    else:
        print(f"No data found for collection '{collection_name}'")
