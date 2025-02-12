from flask import Flask, request, jsonify
import requests
import threading
import time
import json
from src.blockchain.chain import Blockchain
from src.blockchain.block import Block
from src.network.message import Message
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

# Daftar semua node di jaringan
peers = set()

# Inisialisasi blockchain
blockchain = Blockchain()

# Port default
DEFAULT_PORT = 5000

# Fungsi buat resolve konflik (longest chain rule)
def resolve_conflicts():
    """
    Fungsi ini buat ngecek semua blockchain dari node lain dan milih yang paling panjang.
    """
    global blockchain

    longest_chain = blockchain
    for node in peers:
        try:
            response = requests.get(f"{node}/chain")
            if response.status_code == 200:
                length = response.json()['length']
                chain_data = response.json()['chain']

                # Ubah data JSON jadi objek Block
                chain = []
                for block_data in chain_data:
                    block = Block(
                        block_data['index'],
                        block_data['timestamp'],
                        block_data['transactions'],
                        block_data['previous_hash'],
                        block_data['nonce']
                    )
                    chain.append(block)

                # Validasi chain dan pilih yang paling panjang
                if length > len(longest_chain.chain) and blockchain.is_chain_valid():
                    longest_chain.chain = chain
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to node {node}: {e}")

    blockchain = longest_chain
    return True

# Endpoint buat nambah transaksi baru
@app.route('/new_transaction', methods=['POST'])
def new_transaction():
    """
    Endpoint ini buat nerima transaksi baru dari user.
    """
    tx_data = request.get_json()
    required_fields = ["author", "content"]

    for field in required_fields:
        if not tx_data.get(field):
            return "Invalid transaction data", 404

    tx_data["timestamp"] = time.time()
    blockchain.add_new_transaction(tx_data)

    # Sebarkan transaksi ke semua node
    message = Message("new_transaction", tx_data).to_json()
    for node in peers:
        try:
            requests.post(f"{node}/receive_transaction", json=tx_data)
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to node {node}: {e}")

    return "Transaction submitted successfully", 201

# Endpoint buat nerima transaksi dari node lain
@app.route('/receive_transaction', methods=['POST'])
def receive_transaction():
    """
    Endpoint ini buat nerima transaksi dari node lain.
    """
    tx_data = request.get_json()
    blockchain.add_new_transaction(tx_data)
    return "Transaction received", 201

# Endpoint buat nambah blok baru (buat mining)
@app.route('/mine', methods=['GET'])
def mine():
    """
    Endpoint ini buat nambang blok baru.
    """
    new_block = blockchain.mine()
    if new_block:
        # Sebarkan blok baru ke semua node
        message = Message("new_block", new_block.__dict__).to_json()
        for node in peers:
            try:
                requests.post(f"{node}/receive_block", json=new_block.__dict__)
            except requests.exceptions.RequestException as e:
                print(f"Error connecting to node {node}: {e}")
        return "New block mined", 200
    else:
        return "No transactions to mine", 400

# Endpoint buat nerima blok baru dari node lain
@app.route('/receive_block', methods=['POST'])
def receive_block():
    """
    Endpoint ini buat nerima blok baru dari node lain.
    """
    block_data = request.get_json()
    block = Block(
        block_data['index'],
        block_data['timestamp'],
        block_data['transactions'],
        block_data['previous_hash'],
        block_data['nonce']
    )
    if blockchain.is_valid_block(block, blockchain.last_block):
        blockchain.chain.append(block)
        return "Block accepted", 201
    else:
        return "Invalid block", 400

# Endpoint buat daftar node baru
@app.route('/register', methods=['POST'])
def register_node():
    """
    Endpoint ini buat daftar node baru ke jaringan.
    """
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data", 400

    peers.add(node_address)
    return jsonify({'message': 'Node added'}), 201

# Endpoint buat ngambil semua chain
@app.route('/chain', methods=['GET'])
def get_chain():
    """
    Endpoint ini buat ngambil semua chain.
    """
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.__dict__)
    return jsonify({"length": len(chain_data),
                       "chain": chain_data})

# Endpoint buat resolve konflik
@app.route('/resolve', methods=['GET'])
def consensus():
    """
    Endpoint ini buat resolve konflik blockchain.
    """
    if resolve_conflicts():
        return jsonify({'message': 'Our chain was replaced'}), 200
    else:
        return jsonify({'message': 'Our chain is authoritative'}), 200

def start_node(port=DEFAULT_PORT):
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)

if __name__ == '__main__':
    # Dapatkan port dari environment variable, jika ada
    port = int(os.environ.get("PORT", DEFAULT_PORT))
    start_node(port)
