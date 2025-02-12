import os
import json
import time
import threading
import requests
import logging
import secrets
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from typing import List, Union, Dict, Any

# Konfigurasi logging yang fleksibel via environment variable
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO))
logger = logging.getLogger(__name__)

# --- Pengaturan Enkripsi Pesan ---
from cryptography.fernet import Fernet

# Jika NODE_SECRET_KEY tidak diset, generate secara otomatis
SECRET_KEY = os.getenv("NODE_SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = Fernet.generate_key().decode('utf-8')
    logger.warning("NODE_SECRET_KEY tidak di-set. Menggunakan key yang digenerate: %s", SECRET_KEY)
SECRET_KEY = SECRET_KEY.encode('utf-8')
fernet = Fernet(SECRET_KEY)

# Global untuk menyimpan nonce yang sudah digunakan untuk mencegah replay attack
used_nonces = set()

def add_nonce_to_payload(data: dict) -> dict:
    """
    Menambahkan nonce unik ke payload jika belum ada.
    """
    if "nonce" not in data:
        data["nonce"] = secrets.token_hex(8)
    return data

def encrypt_data(data: dict) -> str:
    """
    Meng-enkripsi payload JSON menjadi string terenkripsi.
    Secara otomatis menambahkan nonce untuk mencegah replay attack.
    """
    data_with_nonce = add_nonce_to_payload(data)
    payload = json.dumps(data_with_nonce)
    return fernet.encrypt(payload.encode('utf-8')).decode('utf-8')

def decrypt_data(encrypted_text: str) -> dict:
    """
    Mendekripsi string terenkripsi kembali ke dictionary.
    Memvalidasi bahwa nonce belum pernah digunakan sebelumnya.
    """
    decrypted = fernet.decrypt(encrypted_text.encode('utf-8')).decode('utf-8')
    data = json.loads(decrypted)
    nonce = data.get("nonce")
    if not nonce:
        raise ValueError("Nonce tidak ditemukan dalam payload.")
    if nonce in used_nonces:
        raise ValueError("Payload dengan nonce ini sudah pernah digunakan (replay attack).")
    used_nonces.add(nonce)
    return data

def get_request_data() -> Union[dict, None]:
    """
    Mengembalikan data request. Jika header 'X-Encrypted' diset ke true,
    data didekripsi terlebih dahulu dan divalidasi.
    """
    if request.headers.get("X-Encrypted", "").lower() == "true":
        encrypted_payload = request.get_data(as_text=True)
        try:
            data = decrypt_data(encrypted_payload)
        except Exception as e:
            logger.error("Gagal mendekripsi atau memvalidasi payload: %s", str(e))
            return None
        return data
    else:
        return request.get_json()

# --- Pengaturan Node Registration Secret ---
# Jika NODE_REGISTRATION_SECRET tidak diset, generate secret secara otomatis
NODE_REGISTRATION_SECRET = os.getenv("NODE_REGISTRATION_SECRET")
if not NODE_REGISTRATION_SECRET:
    NODE_REGISTRATION_SECRET = secrets.token_hex(16)
    logger.warning("NODE_REGISTRATION_SECRET tidak di-set. Menggunakan secret yang digenerate: %s", NODE_REGISTRATION_SECRET)
logger.info("NODE_REGISTRATION_SECRET: %s", NODE_REGISTRATION_SECRET)

# --- Fungsi untuk Mengambil Data Blockchain ---
def get_blockchain_data() -> Dict[str, Any]:
    """
    Mengambil data blockchain dalam bentuk dictionary.
    """
    chain_data = [block.__dict__ for block in blockchain.chain]
    return {"length": len(chain_data), "chain": chain_data}

def get_encrypted_response(data: dict) -> Response:
    """
    Mengembalikan Response JSON terenkripsi dari data yang diberikan.
    """
    encrypted_payload = encrypt_data(data)
    return Response(encrypted_payload, status=200, mimetype="text/plain", headers={"X-Encrypted": "true"})

# --- Import komponen blockchain ---
from src.blockchain.chain import Blockchain
from src.blockchain.block import Block, create_genesis_block
from src.network.message import Message

app = Flask(__name__)
CORS(app)

# Daftar node (peers) dalam jaringan
peers: set[str] = set()

# Inisialisasi blockchain
blockchain = Blockchain()

# Lock untuk memastikan thread-safe saat mengubah blockchain
blockchain_lock = threading.Lock()

DEFAULT_PORT = 5000

def resolve_conflicts() -> bool:
    """
    Mengecek blockchain dari node lain dan memilih chain yang paling panjang dan valid.
    Menggunakan aturan longest chain.
    """
    global blockchain
    longest_chain = None
    max_length = len(blockchain.chain)

    for node in peers:
        try:
            resp = requests.get(f"{node}/chain", headers={"X-Encrypted": "true"})
            if resp.status_code == 200:
                data = decrypt_data(resp.text) if resp.headers.get("X-Encrypted", "").lower() == "true" else resp.json()
                length = data.get('length', 0)
                chain_data = data.get('chain', [])
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
                if length > max_length and blockchain.is_chain_valid(chain=candidate_chain):
                    max_length = length
                    longest_chain = candidate_chain
        except requests.exceptions.RequestException as e:
            app.logger.error("Error connecting to node %s: %s", node, str(e))
        except Exception as e:
            app.logger.error("Error processing data from node %s: %s", node, str(e))

    if longest_chain:
        with blockchain_lock:
            blockchain.chain = longest_chain
        return True
    return False

@app.route('/new_transaction', methods=['POST'])
def new_transaction() -> Response:
    """
    Menerima transaksi baru dari user.
    """
    tx_data = request.get_json()
    required_fields = ["author", "content"]
    for field in required_fields:
        if not tx_data.get(field):
            return jsonify({"error": f"Field '{field}' tidak ditemukan"}), 400
    tx_data["timestamp"] = time.time()
    with blockchain_lock:
        blockchain.add_new_transaction(tx_data)
    
    # Sebarkan transaksi ke node lain secara terenkripsi
    msg = Message("new_transaction", tx_data).to_json()
    encrypted_msg = encrypt_data({"message": msg})
    for node in peers:
        try:
            requests.post(f"{node}/receive_transaction", data=encrypted_msg, headers={"X-Encrypted": "true"})
        except requests.exceptions.RequestException as e:
            app.logger.error("Error broadcasting to node %s: %s", node, str(e))
    return jsonify({"message": "Transaction submitted successfully"}), 201

@app.route('/receive_transaction', methods=['POST'])
def receive_transaction() -> Response:
    """
    Menerima transaksi yang disebarkan dari node lain.
    """
    tx_data = get_request_data()
    if tx_data is None:
        return jsonify({"error": "Payload tidak valid atau gagal didekripsi"}), 400
    try:
        inner = json.loads(tx_data.get("message", "{}"))
    except Exception as e:
        logger.error("Gagal parsing payload terenkripsi: %s", str(e))
        return jsonify({"error": "Payload tidak valid"}), 400
    with blockchain_lock:
        blockchain.add_new_transaction(inner)
    return jsonify({"message": "Transaction received"}), 201

@app.route('/mine', methods=['GET'])
def mine() -> Response:
    """
    Melakukan mining untuk membuat blok baru.
    """
    with blockchain_lock:
        new_block = blockchain.mine()

    if new_block:
        block_data = new_block.__dict__
        msg = Message("new_block", block_data).to_json()
        encrypted_msg = encrypt_data({"message": msg})
        for node in peers:
            try:
                requests.post(f"{node}/receive_block", data=encrypted_msg, headers={"X-Encrypted": "true"})
                app.logger.info("Block sent to node %s: %s", node, block_data)
            except requests.exceptions.RequestException as e:
                app.logger.error("Error broadcasting block to node %s: %s", node, str(e))
        return jsonify({"message": "New block mined", "block": block_data}), 200
    else:
        return jsonify({"error": "No transactions to mine"}), 400

@app.route('/receive_block', methods=['POST'])
def receive_block() -> Response:
    """
    Menerima blok baru dari node lain.
    """
    block_payload = get_request_data()
    if block_payload is None:
        return jsonify({"error": "Payload tidak valid atau gagal didekripsi"}), 400
    try:
        inner = json.loads(block_payload.get("message", "{}"))
    except Exception as e:
        logger.error("Gagal parsing payload terenkripsi: %s", str(e))
        return jsonify({"error": "Payload tidak valid"}), 400
    app.logger.info("Received block data: %s", inner)
    block = Block(
        inner.get('index'),
        inner.get('timestamp'),
        inner.get('transactions'),
        inner.get('previous_hash'),
        inner.get('nonce')
    )
    with blockchain_lock:
        if blockchain.is_valid_block(block, blockchain.last_block):
            blockchain.chain.append(block)
            return jsonify({"message": "Block accepted"}), 201
        else:
            return jsonify({"error": "Invalid block"}), 400

@app.route('/register', methods=['POST'])
def register_node() -> Response:
    """
    Mendaftarkan node baru ke dalam jaringan.
    Mencegah serangan Sybil dengan memerlukan 'node_secret' yang valid.
    
    Klien harus mengirimkan JSON dengan:
      - node_address: Alamat node (contoh: http://localhost:5001)
      - node_secret: Jika tidak dikirimkan, akan otomatis dianggap secret yang sama dengan node ini.
    """
    data = request.get_json()
    node_address = data.get("node_address")
    node_secret = data.get("node_secret", NODE_REGISTRATION_SECRET)
    
    if not node_address:
        return jsonify({"error": "node_address harus disediakan"}), 400
    
    if node_secret != NODE_REGISTRATION_SECRET:
        return jsonify({"error": "node_secret tidak valid"}), 400
    
    peers.add(node_address)
    logger.info("Node %s berhasil didaftarkan.", node_address)
    return jsonify({'message': 'Node added', 'peers': list(peers)}), 201

@app.route('/discover', methods=['GET'])
def discover() -> Response:
    """
    Discovery node: Mengembalikan daftar peer yang terdaftar.
    Endpoint ini membantu node baru menemukan node lain di jaringan.
    """
    return jsonify({'peers': list(peers)}), 200

@app.route('/chain', methods=['GET'])
def get_chain_endpoint() -> Response:
    """
    Mengembalikan seluruh chain blockchain secara terenkripsi.
    """
    data = get_blockchain_data()
    return get_encrypted_response(data)

@app.route('/resolve', methods=['GET'])
def consensus() -> Response:
    """
    Melakukan resolve konflik blockchain dengan mengganti chain dengan yang paling panjang.
    Mengembalikan status dalam bentuk terenkripsi.
    """
    replaced = resolve_conflicts()
    payload = {'message': 'Our chain was replaced'} if replaced else {'message': 'Our chain is authoritative'}
    return get_encrypted_response(payload)

@app.route('/', methods=['GET'])
def index() -> Response:
    return jsonify({"message": "ChainKopi Node is running!"}), 200

def start_node(port: int = DEFAULT_PORT) -> None:
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", DEFAULT_PORT))
    start_node(port)
