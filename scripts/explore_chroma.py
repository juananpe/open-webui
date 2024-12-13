import os
import chromadb
from flask import Flask, render_template_string, jsonify
from chromadb.config import Settings

app = Flask(__name__)

# Configure ChromaDB client
CHROMA_DATA_PATH = "../backend/data/vector_db"  # Adjust this path to point to your ChromaDB data directory

client = chromadb.PersistentClient(
    path=CHROMA_DATA_PATH,
    settings=Settings(
        allow_reset=True,
        anonymized_telemetry=False
    )
)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>ChromaDB Explorer</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 20px;
            background-color: #f5f5f5;
        }
        .collection { 
            border: 1px solid #ddd; 
            margin: 10px 0; 
            padding: 15px;
            border-radius: 5px;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metadata { 
            background-color: #f8f8f8;
            padding: 10px;
            margin: 5px 0;
            border-radius: 3px;
            font-family: monospace;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        .document {
            margin: 10px 0;
            padding: 10px;
            background-color: #fff;
            border: 1px solid #eee;
            border-radius: 3px;
        }
        h2 { 
            color: #333;
            margin-top: 0;
        }
        .count { 
            color: #666;
            font-size: 0.9em;
        }
        details {
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 5px;
            background-color: white;
        }
        summary {
            padding: 10px;
            cursor: pointer;
            background-color: #f0f0f0;
            border-radius: 5px;
            font-weight: bold;
        }
        summary:hover {
            background-color: #e8e8e8;
        }
        .details-content {
            padding: 15px;
        }
        .collection-name {
            font-size: 1.2em;
            color: #2c3e50;
        }
        pre {
            margin: 0;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
    </style>
</head>
<body>
    <h1>ChromaDB Explorer</h1>
    
    <div id="collections">
        {% for collection in collections %}
        <div class="collection">
            <h2>
                <span class="collection-name">{{ collection.name }}</span>
                <span class="count">({{ collection.count }} documents)</span>
            </h2>
            
            <details>
                <summary>Collection Metadata</summary>
                <div class="details-content">
                    <div class="metadata">
                        <pre>{{ collection.metadata | tojson(indent=2) }}</pre>
                    </div>
                </div>
            </details>

            <details>
                <summary>Documents</summary>
                <div class="details-content">
                    {% for doc in collection.documents %}
                    <div class="document">
                        <strong>ID:</strong> {{ doc.id }}<br>
                        <strong>Content:</strong> {{ doc.document }}<br>
                        <details>
                            <summary>Document Metadata</summary>
                            <div class="metadata">
                                <pre>{{ doc.metadata | tojson(indent=2) }}</pre>
                            </div>
                        </details>
                    </div>
                    {% endfor %}
                </div>
            </details>
        </div>
        {% endfor %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    collections_data = []
    collections = client.list_collections()
    
    for collection in collections:
        data = collection.get()
        
        documents = []
        for i in range(len(data['ids'])):
            documents.append({
                'id': data['ids'][i],
                'document': data['documents'][i],
                'metadata': data['metadatas'][i] if data['metadatas'] else {}
            })
        
        collections_data.append({
            'name': collection.name,
            'metadata': collection.metadata,
            'count': len(documents),
            'documents': documents
        })
    
    return render_template_string(HTML_TEMPLATE, collections=collections_data)

@app.route('/api/collections')
def get_collections():
    collections_data = []
    collections = client.list_collections()
    
    for collection in collections:
        data = collection.get()
        collections_data.append({
            'name': collection.name,
            'metadata': collection.metadata,
            'count': len(data['ids']),
            'documents': data
        })
    
    return jsonify(collections_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4444, debug=True)