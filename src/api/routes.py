from flask import Flask, jsonify
from flask_cors import CORS
from src.blockchain.chain import Blockchain

app = Flask(__name__)
CORS(app) # Enable CORS

blockchain = Blockchain()

@app.route('/chain', methods=['GET'])
def get_chain():
    """Mengembalikan seluruh rantai blockchain."""
    chain_data = []
    for block in blockchain.chain:
        chain_data.append({
            "index": block.index,
            "timestamp": block.timestamp,
            "transactions": block.transactions,
            "previous_hash": block.previous_hash,
            "hash": block.hash
        })
    return jsonify({"length": len(chain_data),
                    "chain": chain_data})

@app.route('/', methods=['GET'])
def index():
    return "ChainKopi API is running!"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
