import chromadb
from flask import Flask, render_template_string, jsonify, request
from chromadb.config import Settings

app = Flask(__name__)

# Configure ChromaDB client
CHROMA_DATA_PATH = "../backend/data/vector_db"

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
    <title>ChromaDB Metadata Manager</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        select {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin-bottom: 10px;
        }
        button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background-color: #45a049;
        }
        #status {
            margin-top: 20px;
            padding: 10px;
            border-radius: 4px;
        }
        .success {
            background-color: #dff0d8;
            color: #3c763d;
            border: 1px solid #d6e9c6;
        }
        .error {
            background-color: #f2dede;
            color: #a94442;
            border: 1px solid #ebccd1;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>ChromaDB Metadata Manager</h1>
        
        <div class="form-group">
            <label for="sourceCollection">Source Collection:</label>
            <select id="sourceCollection">
                <option value="">Select source collection...</option>
                {% for collection in collections %}
                <option value="{{ collection }}">{{ collection }}</option>
                {% endfor %}
            </select>
        </div>

        <div class="form-group">
            <label for="destCollection">Destination Collection:</label>
            <select id="destCollection">
                <option value="">Select destination collection...</option>
                {% for collection in collections %}
                <option value="{{ collection }}">{{ collection }}</option>
                {% endfor %}
            </select>
        </div>

        <button onclick="replaceMetadata()">Replace Metadata</button>
        
        <div id="status"></div>
    </div>

    <script>
    function replaceMetadata() {
        const sourceCollection = document.getElementById('sourceCollection').value;
        const destCollection = document.getElementById('destCollection').value;
        const statusDiv = document.getElementById('status');
        
        if (!sourceCollection || !destCollection) {
            statusDiv.className = 'error';
            statusDiv.textContent = 'Please select both source and destination collections.';
            return;
        }

        statusDiv.textContent = 'Processing...';
        statusDiv.className = '';

        fetch('/replace_metadata', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                source_collection: sourceCollection,
                dest_collection: destCollection
            })
        })
        .then(response => response.json())
        .then(data => {
            statusDiv.className = data.success ? 'success' : 'error';
            statusDiv.textContent = data.message;
        })
        .catch(error => {
            statusDiv.className = 'error';
            statusDiv.textContent = 'Error: ' + error;
        });
    }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    collections = [col.name for col in client.list_collections()]
    return render_template_string(HTML_TEMPLATE, collections=collections)

@app.route('/replace_metadata', methods=['POST'])
def replace_metadata():
    try:
        data = request.get_json()
        source_collection_name = data['source_collection']
        dest_collection_name = data['dest_collection']

        source_collection = client.get_collection(source_collection_name)
        dest_collection = client.get_collection(dest_collection_name)

        # Get all documents from source collection
        source_data = source_collection.get()
        # Get all documents from destination collection
        dest_data = dest_collection.get()

        updates_count = 0
        
        # Create dictionaries for easier lookup
        source_docs = {
            (meta['name'], meta['start_index']): (id, meta)
            for id, meta in zip(source_data['ids'], source_data['metadatas'])
            if 'name' in meta and 'start_index' in meta
        }

        # Process each document in destination collection
        for i, (dest_id, dest_meta) in enumerate(zip(dest_data['ids'], dest_data['metadatas'])):
            if 'name' in dest_meta and 'start_index' in dest_meta:
                key = (dest_meta['name'], dest_meta['start_index'])
                if key in source_docs:
                    # Update metadata for matching document
                    _, source_metadata = source_docs[key]
                    dest_collection.update(
                        ids=[dest_id],
                        metadatas=[source_metadata]
                    )
                    updates_count += 1

        return jsonify({
            'success': True,
            'message': f'Successfully updated metadata for {updates_count} documents.'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5555, debug=True)