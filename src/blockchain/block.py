import hashlib
import time
import json

class Block:
    def __init__(self, index, timestamp, transactions, previous_hash, nonce=0):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        """Menghitung hash blok berdasarkan data di dalamnya."""
        data = str(self.index) + str(self.timestamp) + json.dumps(self.transactions) + str(self.previous_hash) + str(self.nonce)
        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def __repr__(self):
        return f"Block #{self.index}: Hash = {self.hash[:10]}..."

def create_genesis_block():
    """Membuat blok pertama (Genesis Block)."""
    return Block(0, time.time(), [], "0")

if __name__ == '__main__':
    genesis_block = create_genesis_block()
    print(genesis_block)
    new_block = Block(1, time.time(), ["transaksi 1", "transaksi 2"], genesis_block.hash)
    print(new_block)
