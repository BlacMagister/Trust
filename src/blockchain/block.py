import hashlib
import time
import json
from typing import List, Any

class Block:
    def __init__(self, index: int, timestamp: float, transactions: List[Any], previous_hash: str, nonce: int = 0) -> None:
        """
        Inisialisasi blok baru.

        Args:
            index (int): Nomor urut blok.
            timestamp (float): Waktu pembuatan blok.
            transactions (List[Any]): Daftar transaksi dalam blok.
            previous_hash (str): Hash blok sebelumnya.
            nonce (int, optional): Nilai nonce untuk bukti kerja. Default 0.
        """
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        """
        Menghitung hash blok berdasarkan data di dalamnya menggunakan SHA-256.

        Returns:
            str: Hash blok dalam bentuk string heksadesimal.
        """
        # Mengumpulkan konten blok yang akan dihitung hash-nya
        block_contents = {
            'index': self.index,
            'timestamp': self.timestamp,
            'transactions': self.transactions,
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
        }
        # Mengubah dictionary ke string JSON dengan urutan kunci yang konsisten
        block_string = json.dumps(block_contents, sort_keys=True)
        return hashlib.sha256(block_string.encode('utf-8')).hexdigest()

    def __repr__(self) -> str:
        return f"Block #{self.index}: Hash = {self.hash[:10]}..."

    def __str__(self) -> str:
        return (
            f"Block #{self.index}\n"
            f"Timestamp      : {self.timestamp}\n"
            f"Transactions   : {self.transactions}\n"
            f"Previous Hash  : {self.previous_hash}\n"
            f"Nonce          : {self.nonce}\n"
            f"Hash           : {self.hash}"
        )

def create_genesis_block() -> Block:
    """
    Membuat blok pertama (Genesis Block) dari blockchain.

    Returns:
        Block: Genesis block.
    """
    # Timestamp dapat disesuaikan jika ingin nilai tetap untuk genesis block
    return Block(0, time.time(), [], "0")

if __name__ == '__main__':
    genesis_block = create_genesis_block()
    print("Genesis Block:")
    print(genesis_block)
    new_block = Block(1, time.time(), ["transaksi 1", "transaksi 2"], genesis_block.hash)
    print("\nNew Block:")
    print(new_block)
