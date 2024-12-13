import os
import sys
import sqlite3
import chromadb
from chromadb.config import Settings
import json
from tabulate import tabulate
from typing import Dict, List, Any
from flask import Flask, render_template_string, jsonify, request

# Configure paths - adjust these based on your setup
SQLITE_PATH = "../backend/data/webui.db"
CHROMA_PATH = "../backend/data/vector_db"

# HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Database Explorer</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <style>
        .json-view {
            font-family: monospace;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        .collection-card:hover {
            transform: translateY(-2px);
            transition: all 0.2s ease;
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
        #chromaContent {
            transition: all 0.3s ease;
        }
    </style>
</head>
<body class="bg-gray-100 min-h-screen">
    <div class="container mx-auto px-4 py-8">
        <h1 class="text-3xl font-bold mb-8">Database Explorer</h1>
        
        <!-- Knowledge Bases Section -->
        <div class="mb-12">
            <h2 class="text-2xl font-semibold mb-4">Knowledge Bases (SQLite)</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {% for kb in knowledge_bases %}
                <div class="bg-white rounded-lg shadow-md p-6 collection-card">
                    <h3 class="text-lg font-semibold mb-2">{{ kb.name }}</h3>
                    <p class="text-gray-600 mb-2">{{ kb.description or 'No description' }}</p>
                    <div class="text-sm text-gray-500">
                        <p>ID: {{ kb.id[:8] }}...</p>
                        <p>User ID: {{ kb.user_id }}</p>
                        <p>Files: {{ kb.file_count }}</p>
                    </div>
                    <button 
                        onclick="showKBDetails('{{ kb.id }}', '{{ kb.name }}')"
                        class="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
                    >
                        View Details
                    </button>
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- ChromaDB Details Section -->
        <div id="chromaSection" class="mb-12 hidden">
            <h2 class="text-2xl font-semibold mb-4">
                ChromaDB Contents: <span id="selectedKBName" class="text-blue-600"></span>
            </h2>
            <div id="chromaContent" class="bg-white rounded-lg shadow-md p-6">
                <!-- ChromaDB collections will be inserted here -->
            </div>
        </div>
    </div>

    <script>
        function showKBDetails(kbId, kbName) {
            // Update selected KB name
            document.getElementById('selectedKBName').textContent = kbName;
            
            // Show the ChromaDB section
            document.getElementById('chromaSection').classList.remove('hidden');
            
            // Scroll to ChromaDB section smoothly
            document.getElementById('chromaSection').scrollIntoView({ 
                behavior: 'smooth',
                block: 'start'
            });

            // Fetch and display data
            fetch(`/api/kb/${kbId}`)
                .then(response => response.json())
                .then(data => {
                    const chromaContent = document.getElementById('chromaContent');
                    chromaContent.innerHTML = ''; // Clear previous content
                    
                    if (data.collections.length === 0) {
                        chromaContent.innerHTML = `
                            <div class="text-gray-500 text-center py-8">
                                No ChromaDB collections found for this knowledge base
                            </div>
                        `;
                        return;
                    }
                    
                    // Create content for each collection
                    data.collections.forEach(collection => {
                        const collectionDiv = document.createElement('div');
                        collectionDiv.className = 'mb-6';
                        
                        // Collection header with file information
                        const uniqueFiles = new Set();
                        const fileChunks = {};
                        
                        // Process documents to group by source file
                        collection.documents.forEach(doc => {
                            const filename = doc.metadata?.source || doc.metadata?.file_name || 'Unknown file';
                            uniqueFiles.add(filename);
                            if (!fileChunks[filename]) {
                                fileChunks[filename] = [];
                            }
                            fileChunks[filename].push(doc);
                        });

                        const numFiles = uniqueFiles.size;

                        collectionDiv.innerHTML = `
                            <details class="mb-4">
                                <summary class="cursor-pointer p-3 bg-gray-50 hover:bg-gray-100 rounded flex justify-between items-center">
                                    <span>${collection.name}</span>
                                    <span class="text-sm text-gray-600">
                                        ${collection.documents.length} chunks from ${numFiles} files
                                    </span>
                                </summary>
                                <div class="p-4">
                                    <div class="mb-4 text-sm text-gray-600 bg-gray-50 p-3 rounded">
                                        <p class="font-semibold mb-2">Source Files:</p>
                                        ${Array.from(uniqueFiles).map(filename => `
                                            <div class="ml-2">• ${filename} (${fileChunks[filename].length} chunks)</div>
                                        `).join('')}
                                    </div>
                                    
                                    ${Array.from(uniqueFiles).map(filename => `
                                        <details class="mb-4 border rounded">
                                            <summary class="cursor-pointer p-3 bg-gray-50 hover:bg-gray-100">
                                                ${filename} (${fileChunks[filename].length} chunks)
                                            </summary>
                                            <div class="p-4">
                                                ${fileChunks[filename].map(doc => `
                                                    <div class="border-b py-3">
                                                        <div><strong>Chunk ID:</strong> ${doc.id}</div>
                                                        <div class="mt-2"><strong>Content:</strong> ${doc.document}</div>
                                                        <details class="mt-2">
                                                            <summary class="cursor-pointer text-sm text-blue-600">
                                                                View Metadata
                                                            </summary>
                                                            <pre class="metadata mt-2 text-sm">
${JSON.stringify(doc.metadata, null, 2)}
                                                            </pre>
                                                        </details>
                                                    </div>
                                                `).join('')}
                                            </div>
                                        </details>
                                    `).join('')}
                                </div>
                            </details>
                        `;
                        
                        chromaContent.appendChild(collectionDiv);
                    });
                });
        }
    </script>
</body>
</html>
"""

class DBExplorer:
    def __init__(self):
        # Remove SQLite connection from initialization
        # Initialize only ChromaDB client
        self.chroma_client = chromadb.PersistentClient(
            path=CHROMA_PATH,
            settings=Settings(
                allow_reset=True,
                anonymized_telemetry=False
            )
        )

    def get_db(self):
        """Create a new database connection for each request"""
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def get_knowledge_bases(self) -> List[Dict[str, Any]]:
        """Get all knowledge bases from SQLite"""
        conn = self.get_db()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, description, data, user_id FROM knowledge")
            kbs = []
            for row in cursor.fetchall():
                kb = dict(row)
                try:
                    data = json.loads(kb["data"]) if kb["data"] else {}
                    kb["file_count"] = len(data.get("file_ids", []))
                except json.JSONDecodeError:
                    kb["file_count"] = 0
                kbs.append(kb)
            return kbs
        finally:
            conn.close()

    def get_chroma_collections(self) -> List[Dict[str, Any]]:
        """Get all collections from ChromaDB with their details"""
        collections = []
        for col in self.chroma_client.list_collections():
            try:
                details = self.get_chroma_collection_details(col.name)
                collections.append({
                    "name": col.name,
                    "count": details["count"],
                    "has_metadata": "Yes" if any(details["metadata"]) else "No"
                })
            except Exception as e:
                collections.append({
                    "name": col.name,
                    "count": "ERROR",
                    "has_metadata": "ERROR"
                })
        return collections

    def get_chroma_collection_details(self, collection_name: str) -> Dict[str, Any]:
        """Get details of a specific ChromaDB collection"""
        collection = self.chroma_client.get_collection(name=collection_name)
        data = collection.get()
        return {
            "count": len(data["ids"]),
            "ids": data["ids"],
            "metadata": data["metadatas"],
            "documents": data["documents"]
        }

    def get_kb_details(self, kb_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific knowledge base and its ChromaDB contents"""
        conn = self.get_db()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM knowledge WHERE id = ?", (kb_id,))
            kb = dict(cursor.fetchone())
            
            # Get all ChromaDB collections that might be related to this KB
            collections_data = []
            all_collections = self.chroma_client.list_collections()
            
            # Look for collections that match the KB ID pattern
            matching_collections = [
                col for col in all_collections 
                if kb_id in col.name
            ]
            
            for collection in matching_collections:
                try:
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
                        'documents': documents
                    })
                except Exception as e:
                    print(f"Error getting collection data: {e}")
            
            return {
                'kb_info': kb,
                'collections': collections_data
            }
            
        finally:
            conn.close()

# Initialize Flask app and explorer
app = Flask(__name__)
explorer = DBExplorer()

@app.route('/')
def index():
    knowledge_bases = explorer.get_knowledge_bases()
    chroma_collections = explorer.get_chroma_collections()
    return render_template_string(
        HTML_TEMPLATE,
        knowledge_bases=knowledge_bases,
        chroma_collections=chroma_collections
    )

@app.route('/api/kb/<kb_id>')
def kb_details(kb_id):
    return jsonify(explorer.get_kb_details(kb_id))

@app.route('/api/collection/<collection_name>')
def collection_details(collection_name):
    return jsonify(explorer.get_chroma_collection_details(collection_name))

if __name__ == "__main__":
    try:
        app.run(host='0.0.0.0', port=5001, debug=True)
    except Exception as e:
        print(f"Error: {str(e)}") 