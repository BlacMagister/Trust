import time
import secrets
import logging
from typing import List, Union

from src.blockchain.block import Block, create_genesis_block
from src.blockchain.consensus import validate_block

# Konfigurasi logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Blockchain:
    """
    Implementasi sederhana Blockchain.
    """
    def __init__(self) -> None:
        # Inisialisasi chain dengan genesis block dan list transaksi yang belum dikonfirmasi
        self.chain: List[Block] = [create_genesis_block()]
        self.unconfirmed_transactions: List[dict] = []

    def add_new_transaction(self, transaction: dict) -> None:
        """
        Menambahkan transaksi baru ke daftar transaksi yang belum dikonfirmasi.
        """
        self.unconfirmed_transactions.append(transaction)

    def proof_of_work(self, block: Block, difficulty: int = 2) -> Block:
        """
        Algoritma Proof-of-Work sederhana.
        
        Mencari nonce sehingga hash blok dimulai dengan '0' sebanyak nilai difficulty.
        
        Args:
            block (Block): Blok yang akan ditambang.
            difficulty (int): Tingkat kesulitan mining (default 2).
        
        Returns:
            Block: Blok yang sudah memiliki nonce dan hash valid.
        """
        block.nonce = 0
        computed_hash = block.calculate_hash()
        while not computed_hash.startswith('0' * difficulty):
            block.nonce += 1
            computed_hash = block.calculate_hash()
        block.hash = computed_hash
        return block

    def mine(self) -> Union[Block, bool]:
        """
        Melakukan mining blok baru berdasarkan transaksi yang belum dikonfirmasi.
        
        Proses:
        - Jika tidak ada transaksi, kembalikan False.
        - Buat blok baru dengan index berikutnya, timestamp saat ini, daftar transaksi (copy), dan previous_hash.
        - Lakukan proof-of-work untuk menemukan nonce yang valid.
        - Validasi blok menggunakan fungsi validate_block.
        - Jika valid, tambahkan ke chain dan reset daftar transaksi.
        
        Returns:
            Block: Blok baru yang berhasil ditambang.
            bool: False jika tidak ada transaksi atau blok gagal divalidasi.
        """
        if not self.unconfirmed_transactions:
            logger.info("Tidak ada transaksi untuk ditambang.")
            return False

        last_block = self.chain[-1]
        new_block = Block(
            index=last_block.index + 1,
            timestamp=time.time(),
            transactions=self.unconfirmed_transactions.copy(),
            previous_hash=last_block.hash,
            nonce=0  # Inisialisasi nonce
        )

        # Lakukan proof-of-work untuk menemukan hash yang valid
        new_block = self.proof_of_work(new_block)

        # Validasi blok dengan blok terakhir
        if validate_block(new_block, last_block):
            self.chain.append(new_block)
            self.unconfirmed_transactions = []
            logger.info(f"Blok {new_block.index} berhasil ditambang dengan nonce {new_block.nonce}.")
            return new_block
        else:
            logger.error("Validasi blok baru gagal.")
            return False

    def add_block(self, block: Block) -> None:
        """
        Menambahkan blok baru ke dalam chain.
        Proses ini akan memperbarui field previous_hash dan hash blok.
        
        Args:
            block (Block): Blok yang akan ditambahkan.
        """
        block.previous_hash = self.chain[-1].hash
        block.hash = block.calculate_hash()
        self.chain.append(block)
        logger.info(f"Blok {block.index} telah ditambahkan ke chain.")

    def is_chain_valid(self, chain: List[Block] = None) -> bool:
        """
        Memvalidasi integritas chain blockchain.
        
        Jika tidak ada chain yang diberikan, akan divalidasi terhadap chain milik instance.
        
        Args:
            chain (List[Block], optional): Chain yang akan divalidasi. Default None.
        
        Returns:
            bool: True jika chain valid, False jika tidak.
        """
        if chain is None:
            chain = self.chain

        if not chain:
            logger.error("Chain kosong.")
            return False

        # Validasi genesis block
        genesis_block = chain[0]
        if genesis_block.hash != create_genesis_block().hash:
            logger.error("Genesis block tidak valid.")
            return False

        for i in range(1, len(chain)):
            current_block = chain[i]
            previous_block = chain[i - 1]

            if current_block.hash != current_block.calculate_hash():
                logger.error("Hash blok %d tidak valid.", current_block.index)
                return False

            if current_block.previous_hash != previous_block.hash:
                logger.error("Previous hash pada blok %d tidak valid.", current_block.index)
                return False

            if not validate_block(current_block, previous_block):
                logger.error("Blok %d gagal validasi konsensus.", current_block.index)
                return False

        logger.info("Chain valid.")
        return True

    @property
    def last_block(self) -> Block:
        """
        Mengembalikan blok terakhir dalam chain.
        
        Returns:
            Block: Blok terakhir.
        """
        return self.chain[-1]

    def is_valid_block(self, block: Block, last_block: Block) -> bool:
        """
        Validasi sebuah blok terhadap blok sebelumnya.
        
        Args:
            block (Block): Blok yang akan divalidasi.
            last_block (Block): Blok sebelumnya.
        
        Returns:
            bool: True jika blok valid, False jika tidak.
        """
        return validate_block(block, last_block)

    def __repr__(self) -> str:
        return f"Blockchain dengan {len(self.chain)} blok. Valid: {self.is_chain_valid()}"
