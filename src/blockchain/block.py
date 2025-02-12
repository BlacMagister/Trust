import hashlib
import time
import json
from typing import List

class Transaction:
    def __init__(self, sender: str, recipient: str, amount: float, timestamp: float = None) -> None:
        """
        Inisialisasi transaksi.

        Args:
            sender (str): Pengirim.
            recipient (str): Penerima.
            amount (float): Jumlah yang dikirim.
            timestamp (float, optional): Waktu transaksi. Jika tidak diberikan, akan diisi waktu saat ini.
        """
        self._sender = sender
        self._recipient = recipient
        self._amount = amount
        self._timestamp = timestamp if timestamp is not None else time.time()

    @property
    def sender(self) -> str:
        return self._sender

    @property
    def recipient(self) -> str:
        return self._recipient

    @property
    def amount(self) -> float:
        return self._amount

    @property
    def timestamp(self) -> float:
        return self._timestamp

    def validate(self) -> bool:
        """
        Validasi dasar transaksi:
         - Sender dan recipient harus berupa string non‑kosong.
         - Amount harus berupa nilai numerik positif.

        Returns:
            bool: True jika transaksi valid, False jika tidak.
        """
        if not isinstance(self._sender, str) or not self._sender:
            return False
        if not isinstance(self._recipient, str) or not self._recipient:
            return False
        if not isinstance(self._amount, (int, float)) or self._amount <= 0:
            return False
        return True

    def to_dict(self) -> dict:
        """
        Mengubah transaksi menjadi dictionary.

        Returns:
            dict: Representasi dictionary dari transaksi.
        """
        return {
            "sender": self._sender,
            "recipient": self._recipient,
            "amount": self._amount,
            "timestamp": self._timestamp
        }

    def __repr__(self) -> str:
        return f"Transaction(from={self._sender}, to={self._recipient}, amount={self._amount})"


class Block:
    def __init__(self, index: int, timestamp: float, transactions: List[Transaction], previous_hash: str, nonce: int = 0) -> None:
        """
        Inisialisasi blok baru.

        Args:
            index (int): Nomor urut blok.
            timestamp (float): Waktu pembuatan blok.
            transactions (List[Transaction]): Daftar transaksi dalam blok.
            previous_hash (str): Hash blok sebelumnya.
            nonce (int, optional): Nilai nonce untuk bukti kerja. Default 0.
        """
        self._index = index
        self._timestamp = timestamp
        self._transactions = transactions
        self._previous_hash = previous_hash
        self._nonce = nonce
        self._hash = self.calculate_hash()

    @property
    def index(self) -> int:
        return self._index

    @property
    def timestamp(self) -> float:
        return self._timestamp

    @property
    def transactions(self) -> List[Transaction]:
        return self._transactions

    @property
    def previous_hash(self) -> str:
        return self._previous_hash

    @property
    def nonce(self) -> int:
        return self._nonce

    @property
    def hash(self) -> str:
        return self._hash

    def calculate_hash(self) -> str:
        """
        Menghitung hash blok berdasarkan data di dalamnya menggunakan SHA3-256.

        Proses validasi:
         - Setiap transaksi harus valid (memanggil metode validate() pada objek Transaction).
         - Jika ada transaksi tidak valid, maka akan mengeluarkan ValueError.

        Returns:
            str: Hash blok dalam bentuk string heksadesimal.
        """
        # Validasi setiap transaksi
        for tx in self._transactions:
            if not tx.validate():
                raise ValueError("Invalid transaction detected during hash calculation")
        block_contents = {
            'index': self._index,
            'timestamp': self._timestamp,
            'transactions': [tx.to_dict() for tx in self._transactions],
            'previous_hash': self._previous_hash,
            'nonce': self._nonce,
        }
        # Pastikan urutan kunci konsisten dengan sort_keys=True
        block_string = json.dumps(block_contents, sort_keys=True)
        # Menggunakan SHA3-256 untuk keamanan yang lebih tinggi
        return hashlib.sha3_256(block_string.encode('utf-8')).hexdigest()

    def __repr__(self) -> str:
        return f"Block #{self._index}: Hash = {self._hash[:10]}..."

    def __str__(self) -> str:
        return (
            f"Block #{self._index}\n"
            f"Timestamp      : {self._timestamp}\n"
            f"Transactions   : {self._transactions}\n"
            f"Previous Hash  : {self._previous_hash}\n"
            f"Nonce          : {self._nonce}\n"
            f"Hash           : {self._hash}"
        )


def create_genesis_block() -> Block:
    """
    Membuat blok pertama (Genesis Block) dari blockchain.

    Returns:
        Block: Genesis block.
    """
    return Block(0, time.time(), [], "0")


if __name__ == '__main__':
    # Contoh pembuatan transaksi
    tx1 = Transaction("Alice", "Bob", 50.0)
    tx2 = Transaction("Bob", "Charlie", 25.0)
    print("Sample Transactions:")
    print(tx1)
    print(tx2)
    
    # Membuat genesis block
    genesis_block = create_genesis_block()
    print("\nGenesis Block:")
    print(genesis_block)
    
    # Membuat blok baru dengan transaksi
    new_block = Block(1, time.time(), [tx1, tx2], genesis_block.hash)
    print("\nNew Block:")
    print(new_block)
