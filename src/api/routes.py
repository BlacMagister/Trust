import os
import logging
from flask import Flask, jsonify, Response
from flask_cors import CORS
from typing import Dict, Any, List

# Import komponen blockchain
from src.blockchain.chain import Blockchain

app = Flask(__name__)
CORS(app)  # Enable CORS

# Konfigurasi logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inisialisasi blockchain
blockchain = Blockchain()

def serialize_block(block: Any) -> Dict[str, Any]:
    """
    Mengubah objek block menjadi dictionary.
    
    Args:
        block: Objek block.
        
    Returns:
        dict: Representasi dictionary dari block.
    """
    return {
        "index": block.index,
        "timestamp": block.timestamp,
        "transactions": block.transactions,
        "previous_hash": block.previous_hash,
        "hash": block.hash
    }

@app.route('/chain', methods=['GET'])
def get_chain() -> Response:
    """
    Mengembalikan seluruh blockchain dalam format JSON.
    
    Returns:
        Response: JSON yang berisi panjang chain dan list block.
    """
    chain_data: List[Dict[str, Any]] = [serialize_block(block) for block in blockchain.chain]
    response = {
        "length": len(chain_data),
        "chain": chain_data
    }
    return jsonify(response), 200

@app.route('/', methods=['GET'])
def index() -> Response:
    """
    Endpoint utama yang mengembalikan pesan bahwa API berjalan.
    
    Returns:
        Response: Pesan string.
    """
    return jsonify({"message": "ChainKopi API is running!"}), 200

if __name__ == '__main__':
    # Gunakan environment variable PORT jika ada, default ke 5002
    port = int(os.environ.get("PORT", 5002))
    logger.info("Starting API on port %s", port)
    app.run(debug=True, host='0.0.0.0', port=port)
