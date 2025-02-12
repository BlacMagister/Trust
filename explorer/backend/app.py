import os
import json
import time
import logging
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from typing import List, Dict, Any

# Import Block dan create_genesis_block dari modul blockchain
from src.blockchain.block import Block, create_genesis_block

# Konfigurasi logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Blockchain:
    """
    Implementasi blockchain sederhana.
    
    Atribut:
      - chain: List of Block, berisi seluruh blok dalam chain.
    """
    def __init__(self) -> None:
        self.chain: List[Block] = [create_genesis_block()]
        logger.info("Genesis block created.")

    def add_block(self, block: Block) -> None:
        """
        Menambahkan blok ke chain setelah mengupdate previous_hash dan menghitung ulang hash.
        
        Args:
            block (Block): Blok yang akan ditambahkan.
        """
        # Set previous_hash dari blok baru ke hash blok terakhir
        block.previous_hash = self.chain[-1].hash
        # Hitung ulang hash untuk memastikan integritas
        block.hash = block.calculate_hash()
        # (Opsional: validasi tambahan bisa ditambahkan di sini)
        self.chain.append(block)
        logger.info("Block %d added to chain.", block.index)

    def is_chain_valid(self) -> bool:
        """
        Memvalidasi integritas chain.
        
        Returns:
            bool: True jika chain valid, False jika tidak.
        """
        for i in range(1, len(self.chain)):
            current_block: Block = self.chain[i]
            previous_block: Block = self.chain[i - 1]
            if current_block.hash != current_block.calculate_hash():
                logger.error("Hash mismatch on block %d.", current_block.index)
                return False
            if current_block.previous_hash != previous_block.hash:
                logger.error("Previous hash mismatch on block %d.", current_block.index)
                return False
        return True

    def __repr__(self) -> str:
        return f"Blockchain with {len(self.chain)} blocks. Valid: {self.is_chain_valid()}"

# Inisialisasi blockchain dan tambahkan beberapa blok untuk contoh
blockchain = Blockchain()
new_block = Block(1, time.time(), ["transaksi 1", "transaksi 2"], blockchain.chain[-1].hash)
blockchain.add_block(new_block)

new_block_2 = Block(2, time.time(), ["transaksi 3", "transaksi 4"], blockchain.chain[-1].hash)
blockchain.add_block(new_block_2)

# Inisialisasi Flask app dengan static folder (misal, dari folder frontend)
app = Flask(__name__, static_folder='../frontend')
CORS(app)

@app.route('/blocks', methods=['GET'])
def get_blocks() -> Any:
    """
    Endpoint untuk mengembalikan seluruh blockchain dalam format JSON.
    
    Returns:
        Response JSON: Berisi panjang chain, list blok, dan status validitas chain.
    """
    blocks_data: List[Dict[str, Any]] = [
        {
            "index": block.index,
            "timestamp": block.timestamp,
            "transactions": block.transactions,
            "previous_hash": block.previous_hash,
            "hash": block.hash
        } for block in blockchain.chain
    ]
    response = {
        "length": len(blocks_data),
        "chain": blocks_data,
        "valid": blockchain.is_chain_valid()
    }
    return jsonify(response), 200

@app.route('/block/<int:index>', methods=['GET'])
def get_block(index: int) -> Any:
    """
    Endpoint untuk mengembalikan data blok tertentu berdasarkan indeks.
    
    Args:
        index (int): Indeks blok yang diminta.
    
    Returns:
        Response JSON: Data blok jika ditemukan, atau error message.
    """
    try:
        block = blockchain.chain[index]
        block_data = {
            "index": block.index,
            "timestamp": block.timestamp,
            "transactions": block.transactions,
            "previous_hash": block.previous_hash,
            "hash": block.hash
        }
        return jsonify(block_data), 200
    except IndexError:
        logger.error("Block with index %d not found.", index)
        return jsonify({"error": "Block not found"}), 404

@app.route('/')
def serve_index() -> Any:
    """
    Serve file index.html dari folder static.
    
    Returns:
        File index.html.
    """
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    logger.info("Starting server on port %d", port)
    app.run(debug=True, host='0.0.0.0', port=port)
