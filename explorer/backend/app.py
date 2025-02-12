from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from src.blockchain.block import Block, create_genesis_block
import time
import os

class Blockchain:
    def __init__(self):
        self.chain = [create_genesis_block()]

    def add_block(self, block):
        block.previous_hash = self.chain[-1].hash
        block.hash = block.calculate_hash()
        self.chain.append(block)

    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]

            if current_block.hash != current_block.calculate_hash():
                return False

            if current_block.previous_hash != previous_block.hash:
                return False

        return True

    def __repr__(self):
          return f"Blockchain with {len(self.chain)} blocks. Valid: {self.is_chain_valid()}"


blockchain = Blockchain()
new_block = Block(1, time.time(), ["transaksi 1", "transaksi 2"], blockchain.chain[-1].hash)
blockchain.add_block(new_block)

new_block_2 = Block(2, time.time(), ["transaksi 3", "transaksi 4"], blockchain.chain[-1].hash)
blockchain.add_block(new_block_2)

app = Flask(__name__, static_folder='../frontend') # Serve static files from frontend
CORS(app)

@app.route('/blocks', methods=['GET'])
def get_blocks():
    blocks_data = [{'index': block.index,
                    'timestamp': block.timestamp,
                    'transactions': block.transactions,
                    'previous_hash': block.previous_hash,
                    'hash': block.hash} for block in blockchain.chain]
    return jsonify(blocks_data)

@app.route('/block/<int:index>', methods=['GET'])
def get_block(index):
    try:
        block = blockchain.chain[index]
        block_data = {'index': block.index,
                    'timestamp': block.timestamp,
                    'transactions': block.transactions,
                    'previous_hash': block.previous_hash,
                    'hash': block.hash}
        return jsonify(block_data)
    except IndexError:
        return jsonify({'error': 'Block not found'}), 404

@app.route('/')
def serve_index():
    """Serve the main index.html file."""
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
