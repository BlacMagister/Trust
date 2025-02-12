import time
import secrets
import logging
from typing import List, Union, Dict

from src.blockchain.block import Block, create_genesis_block
from src.blockchain.consensus import validate_block

# Konfigurasi logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Blockchain:
    """
    Implementasi Blockchain sederhana dengan dynamic difficulty adjustment dan validasi transaksi.
    """
    def __init__(self) -> None:
        # Inisialisasi chain dengan genesis block dan pool transaksi yang belum dikonfirmasi
        self.chain: List[Block] = [create_genesis_block()]
        self.unconfirmed_transactions: List[Dict] = []
        self.difficulty: int = 2  # Tingkat kesulitan awal
        self.target_mine_time: float = 10.0  # Target waktu mining dalam detik

    def validate_transaction(self, transaction: dict) -> bool:
        """
        Validasi struktur dan isi transaksi sebelum ditambahkan ke blockchain.

        Args:
            transaction (dict): Transaksi yang akan divalidasi.

        Returns:
            bool: True jika transaksi valid, False jika tidak.
        """
        required_keys = ["sender", "recipient", "amount"]
        for key in required_keys:
            if key not in transaction:
                logger.error("Validasi transaksi gagal: kunci '%s' tidak ditemukan.", key)
                return False
        if not isinstance(transaction["amount"], (int, float)) or transaction["amount"] < 0:
            logger.error("Validasi transaksi gagal: jumlah (%s) tidak valid.", transaction["amount"])
            return False
        # Placeholder: verifikasi digital signature bisa ditambahkan di sini.
        return True

    def add_new_transaction(self, transaction: dict) -> None:
        """
        Menambahkan transaksi baru ke dalam pool transaksi yang belum dikonfirmasi, setelah validasi.

        Args:
            transaction (dict): Transaksi yang akan ditambahkan.
        """
        if self.validate_transaction(transaction):
            self.unconfirmed_transactions.append(transaction)
            logger.info("Transaksi berhasil ditambahkan: %s", transaction)
        else:
            logger.error("Transaksi ditolak: %s", transaction)

    def proof_of_work(self, block: Block) -> Block:
        """
        Algoritma Proof-of-Work untuk menemukan nonce yang membuat hash blok valid berdasarkan difficulty saat ini.

        Args:
            block (Block): Blok yang akan ditambang.

        Returns:
            Block: Blok dengan nonce dan hash yang valid.
        """
        block.nonce = 0
        computed_hash = block.calculate_hash()
        logger.info("Mulai Proof-of-Work untuk blok %d dengan difficulty %d", block.index, self.difficulty)
        while not computed_hash.startswith('0' * self.difficulty):
            block.nonce += 1
            computed_hash = block.calculate_hash()
            # Logging setiap 10.000 iterasi sebagai debug
            if block.nonce % 10000 == 0:
                logger.debug("Nonce: %d, Hash: %s", block.nonce, computed_hash)
        block.hash = computed_hash
        logger.info("Proof-of-Work selesai: nonce = %d, hash = %s", block.nonce, block.hash)
        return block

    def mine(self) -> Union[Block, bool]:
        """
        Melakukan mining blok baru berdasarkan transaksi yang belum dikonfirmasi.

        Proses:
          - Jika tidak ada transaksi, kembalikan False.
          - Buat blok baru dengan index berikutnya, timestamp saat ini, salinan transaksi, dan previous_hash.
          - Lakukan proof-of-work dengan difficulty dinamis.
          - Hitung waktu mining dan adjust difficulty sesuai target.
          - Validasi blok menggunakan fungsi validate_block.
          - Jika valid, tambahkan ke chain, reset pool transaksi, dan kembalikan blok.

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
            nonce=0
        )

        start_time = time.time()
        new_block = self.proof_of_work(new_block)
        end_time = time.time()
        mining_time = end_time - start_time
        logger.info("Blok %d ditambang dalam %.2f detik.", new_block.index, mining_time)

        # Penyesuaian difficulty secara dinamis berdasarkan waktu mining
        if mining_time < self.target_mine_time:
            self.difficulty += 1
            logger.info("Mining terlalu cepat (%.2f detik). Menaikkan difficulty ke %d.", mining_time, self.difficulty)
        elif mining_time > self.target_mine_time and self.difficulty > 1:
            self.difficulty -= 1
            logger.info("Mining terlalu lambat (%.2f detik). Menurunkan difficulty ke %d.", mining_time, self.difficulty)
        else:
            logger.info("Waktu mining optimal (%.2f detik). Difficulty tetap %d.", mining_time, self.difficulty)

        # Validasi blok menggunakan blok sebelumnya
        if validate_block(new_block, last_block):
            self.chain.append(new_block)
            self.unconfirmed_transactions = []
            logger.info("Blok %d berhasil ditambang dan ditambahkan ke chain.", new_block.index)
            return new_block
        else:
            logger.error("Validasi blok %d gagal.", new_block.index)
            return False

    def add_block(self, block: Block) -> None:
        """
        Menambahkan blok baru ke dalam chain dengan memperbarui previous_hash dan hash.

        Args:
            block (Block): Blok yang akan ditambahkan.
        """
        block.previous_hash = self.chain[-1].hash
        block.hash = block.calculate_hash()
        self.chain.append(block)
        logger.info("Blok %d telah ditambahkan ke chain.", block.index)

    def is_chain_valid(self, chain: List[Block] = None) -> bool:
        """
        Memvalidasi integritas chain blockchain.

        Args:
            chain (List[Block], optional): Chain yang akan divalidasi. Default adalah chain instance.

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
