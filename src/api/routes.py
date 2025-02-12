from flask import Flask, jsonify
from src.blockchain.chain import Blockchain  # Import Blockchain class

app = Flask(__name__)
blockchain = Blockchain() # Inisialisasi blockchain

@app.route('/chain', methods=['GET'])
def get_chain():
    """Mengembalikan seluruh rantai blockchain."""
    chain_data = []
    for block in blockchain.chain:
        chain_data.append(block.__dict__)  # Konversi ke dictionary
    return jsonify({"length": len(chain_data),
                    "chain": chain_data})

# Route-rute lain bisa ditambahkan di sini (misalnya, untuk nambah transaksi)

if __name__ == '__main__':
    app.run(debug=True, port=5002)
