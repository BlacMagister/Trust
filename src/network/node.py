from flask import Flask, request, jsonify
import requests
import threading
import time

app = Flask(__name__)

peers = set()

@app.route('/new_transaction', methods=['POST'])
def new_transaction():
  # TODO: Handle new transaction
  return "Transaction received!", 201

@app.route('/register', methods=['POST'])
def register_node():
    node_address = request.get_json()["node_address"]
    if not node_address:
        return "Invalid data", 400

    peers.add(node_address)
    return jsonify({'message': 'Node added'}), 201

@app.route('/resolve', methods=['GET'])
def consensus():
    # TODO: Implement resolve conflict chain logic
    return jsonify({'message': 'Chain resolved'}), 200

def start_node(port):
  app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)

if __name__ == '__main__':
  port = 5000
  start_node(port)
