import os
import logging
from flask import Flask, jsonify, Response, request
from flask_cors import CORS
from typing import Dict, Any, List

# Import komponen blockchain
from src.blockchain.chain import Blockchain
from src.blockchain.block import Block

app = Flask(__name__)
CORS(app)  # Enable CORS

# Konfigurasi logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inisialisasi blockchain
blockchain = Blockchain()

def serialize_block(block: Block) -> Dict[str, Any]:
    """
    Mengubah objek Block menjadi dictionary dengan format yang sesuai.
    
    Args:
        block (Block): Objek blok yang akan diserialisasi.
    
    Returns:
        Dict[str, Any]: Representasi dictionary dari blok.
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
    Endpoint untuk mengembalikan seluruh blockchain dalam format JSON.
    
    Returns:
        Response: JSON yang berisi panjang chain, list blok, dan status validitas.
    """
    try:
        chain_data: List[Dict[str, Any]] = [serialize_block(block) for block in blockchain.chain]
        response = {
            "length": len(chain_data),
            "chain": chain_data,
            "valid": blockchain.is_chain_valid()
        }
        return jsonify(response), 200
    except Exception as e:
        logger.error("Error retrieving blockchain: %s", str(e))
        return jsonify({"error": "Unable to retrieve blockchain data"}), 500

@app.route('/block/<int:index>', methods=['GET'])
def get_block(index: int) -> Response:
    """
    Endpoint untuk mendapatkan data blok berdasarkan indeks.
    
    Args:
        index (int): Indeks blok yang diminta.
    
    Returns:
        Response: JSON data blok jika ditemukan, atau error jika tidak ditemukan.
    """
    try:
        if index < 0 or index >= len(blockchain.chain):
            return jsonify({"error": "Block not found"}), 404
        block = blockchain.chain[index]
        block_data = serialize_block(block)
        return jsonify(block_data), 200
    except Exception as e:
        logger.error("Error retrieving block %d: %s", index, str(e))
        return jsonify({"error": "Unable to retrieve block data"}), 500

@app.route('/health', methods=['GET'])
def health() -> Response:
    """
    Endpoint untuk memeriksa status kesehatan API.
    
    Returns:
        Response: JSON dengan status 'ok' dan pesan API berjalan.
    """
    return jsonify({"status": "ok", "message": "ChainKopi API is running!"}), 200

@app.route('/', methods=['GET'])
def index_route() -> Response:
    """
    Endpoint utama yang menampilkan pesan bahwa API berjalan.
    
    Returns:
        Response: JSON pesan status.
    """
    return jsonify({"message": "ChainKopi API is running!"}), 200

if __name__ == '__main__':
    # Gunakan environment variable PORT jika ada, default ke 5002
    port = int(os.environ.get("PORT", 5002))
    logger.info("Starting API on port %d", port)
    app.run(debug=True, host='0.0.0.0', port=port)
