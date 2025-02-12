import os
import json
import time
import threading
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

# Import komponen blockchain
from src.blockchain.chain import Blockchain
from src.blockchain.block import Block
from src.network.message import Message

app = Flask(__name__)
CORS(app)

# Daftar node (peers) dalam jaringan
peers = set()

# Inisialisasi blockchain
blockchain = Blockchain()

# Lock untuk memastikan thread-safe saat mengubah blockchain
blockchain_lock = threading.Lock()

DEFAULT_PORT = 5000

def resolve_conflicts():
    """
    Mengecek blockchain dari node lain dan memilih chain yang paling panjang dan valid.
    Menggunakan aturan longest chain.
    """
    global blockchain
    longest_chain = None
    max_length = len(blockchain.chain)

    # Iterasi seluruh peer
    for node in peers:
        try:
            response = requests.get(f"{node}/chain")
            if response.status_code == 200:
                data = response.json()
                length = data.get('length', 0)
                chain_data = data.get('chain', [])
                # Ubah data JSON menjadi list objek Block
                candidate_chain = []
                for block_data in chain_data:
                    block = Block(
                        block_data.get('index'),
                        block_data.get('timestamp'),
                        block_data.get('transactions'),
                        block_data.get('previous_hash'),
                        block_data.get('nonce')
                    )
                    candidate_chain.append(block)
                # Cek apakah candidate chain lebih panjang dan valid
                # Asumsi: metode is_chain_valid dapat menerima chain sebagai parameter (sesuaikan jika perlu)
                if length > max_length and blockchain.is_chain_valid(chain=candidate_chain):
                    max_length = length
                    longest_chain = candidate_chain
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Error connecting to node {node}: {e}")

    if longest_chain:
        with blockchain_lock:
            blockchain.chain = longest_chain
        return True
    return False

@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    """
    Menerima transaksi baru dari user.
    """
    tx_data = request.get_json()
    required_fields = ["author", "content"]

    # Validasi input transaksi
    for field in required_fields:
        if not tx_data.get(field):
            return jsonify({"error": f"Field '{field}' tidak ditemukan"}), 400

    tx_data["timestamp"] = time.time()
    with blockchain_lock:
        blockchain.add_new_transaction(tx_data)

    # Sebarkan transaksi ke semua node lain
    msg = Message("new_transaction", tx_data).to_json()
    for node in peers:
        try:
            requests.post(f"{node}/receive_transaction", json=tx_data)
        except requests.exceptions.RequestException as e:
            app.logger.error(f"Error broadcasting to node {node}: {e}")

    return jsonify({"message": "Transaction submitted successfully"}), 201

@app.route('/receive_transaction', methods=['POST'])
def receive_transaction():
    """
    Menerima transaksi yang disebarkan dari node lain.
    """
    tx_data = request.get_json()
    with blockchain_lock:
        blockchain.add_new_transaction(tx_data)
    return jsonify({"message": "Transaction received"}), 201

@app.route('/mine', methods=['GET'])
def mine():
    """
    Melakukan mining untuk membuat blok baru.
    """
    with blockchain_lock:
        new_block = blockchain.mine()

    if new_block:
        block_data = new_block.__dict__
        msg = Message("new_block", block_data).to_json()
        # Sebarkan blok baru ke semua node
        for node in peers:
            try:
                requests.post(f"{node}/receive_block", json=block_data)
            except requests.exceptions.RequestException as e:
                app.logger.error(f"Error broadcasting block to node {node}: {e}")
        return jsonify({"message": "New block mined", "block": block_data}), 200
    else:
        return jsonify({"error": "No transactions to mine"}), 400

@app.route('/receive_block', methods=['POST'])
def receive_block():
    """
    Menerima blok baru dari node lain.
    """
    block_data = request.get_json()
    block = Block(
        block_data.get('index'),
        block_data.get('timestamp'),
        block_data.get('transactions'),
        block_data.get('previous_hash'),
        block_data.get('nonce')
    )
    with blockchain_lock:
        # Validasi blok menggunakan blok terakhir di chain saat ini
        if blockchain.is_valid_block(block, blockchain.last_block):
            blockchain.chain.append(block)
            return jsonify({"message": "Block accepted"}), 201
        else:
            return jsonify({"error": "Invalid block"}), 400

@app.route('/register', methods=['POST'])
def register_node():
    """
    Mendaftarkan node baru ke dalam jaringan.
    """
    data = request.get_json()
    node_address = data.get("node_address")
    if not node_address:
        return jsonify({"error": "Invalid data"}), 400

    peers.add(node_address)
    return jsonify({'message': 'Node added', 'peers': list(peers)}), 201

@app.route('/chain', methods=['GET'])
def get_chain():
    """
    Mengembalikan seluruh chain blockchain.
    """
    chain_data = [block.__dict__ for block in blockchain.chain]
    return jsonify({"length": len(chain_data), "chain": chain_data}), 200

@app.route('/resolve', methods=['GET'])
def consensus():
    """
    Melakukan resolve konflik blockchain dengan mengganti chain dengan yang paling panjang.
    """
    replaced = resolve_conflicts()
    if replaced:
        return jsonify({'message': 'Our chain was replaced'}), 200
    else:
        return jsonify({'message': 'Our chain is authoritative'}), 200

@app.route('/', methods=['GET'])
def index():
    return "ChainKopi Node is running!", 200

def start_node(port=DEFAULT_PORT):
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", DEFAULT_PORT))
    start_node(port)
