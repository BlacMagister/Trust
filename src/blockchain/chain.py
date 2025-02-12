import os
import time
import secrets
import json
import logging
import re
from typing import List, Union, Dict

# Konfigurasi logging yang fleksibel via environment variable
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO))
logger = logging.getLogger(__name__)

# Import untuk verifikasi tanda tangan Ethereum
from eth_account import Account
from eth_account.messages import encode_defunct

# Asumsikan Block dan create_genesis_block diimpor dari modul lain.
from src.blockchain.block import Block, create_genesis_block
from src.blockchain.consensus import validate_block

def is_valid_address(address: str) -> bool:
    """
    Validasi alamat Ethereum.
    Alamat harus berupa string, diawali "0x", panjang 42 karakter, dan merupakan nilai hexadecimal.
    """
    if isinstance(address, str) and address.startswith("0x") and len(address) == 42:
        try:
            int(address[2:], 16)
            return True
        except ValueError:
            return False
    return False

def get_transaction_message(transaction: Dict) -> bytes:
    """
    Menghasilkan pesan (dalam bentuk bytes) dari transaksi dengan mengeluarkan field signature.
    Urutan kunci dijaga dengan sort_keys=True agar konsisten.
    """
    tx_copy = transaction.copy()
    tx_copy.pop("signature", None)
    return json.dumps(tx_copy, sort_keys=True).encode('utf-8')

def verify_eth_signature(transaction: Dict) -> bool:
    """
    Memverifikasi tanda tangan digital transaksi menggunakan eth_account.
    
    Proses:
      - Menghasilkan pesan transaksi (tanpa field signature).
      - Meng-encode pesan tersebut dengan encode_defunct().
      - Meng-recover alamat dari tanda tangan.
      - Membandingkan alamat yang direcover dengan field sender.
    
    Args:
        transaction (dict): Transaksi yang akan diverifikasi.
        
    Returns:
        bool: True jika verifikasi berhasil, False jika tidak.
    """
    try:
        message = get_transaction_message(transaction)
        encoded_msg = encode_defunct(message)
        recovered_addr = Account.recover_message(encoded_msg, signature=transaction["signature"])
        if recovered_addr.lower() == transaction["sender"].lower():
            return True
        else:
            logger.error("Alamat yang direcover (%s) tidak cocok dengan sender (%s).", recovered_addr, transaction["sender"])
            return False
    except Exception as e:
        logger.error("Error saat verifikasi tanda tangan: %s", str(e))
        return False

class Blockchain:
    """
    Implementasi Blockchain sederhana dengan dynamic difficulty adjustment, validasi transaksi,
    serta verifikasi tanda tangan digital.
    """
    def __init__(self) -> None:
        # Inisialisasi chain dengan genesis block dan pool transaksi yang belum dikonfirmasi
        self.chain: List[Block] = [create_genesis_block()]
        self.unconfirmed_transactions: List[Dict] = []
        self.difficulty: int = 2  # Tingkat kesulitan awal
        self.target_mine_time: float = 10.0  # Target waktu mining dalam detik

    def validate_transaction(self, transaction: Dict) -> bool:
        """
        Validasi struktur dan isi transaksi sebelum ditambahkan ke blockchain.
        Termasuk validasi alamat dan verifikasi tanda tangan digital.
        
        Args:
            transaction (dict): Transaksi yang akan divalidasi.
        
        Returns:
            bool: True jika transaksi valid, False jika tidak.
        """
        required_keys = ["sender", "recipient", "amount", "signature"]
        for key in required_keys:
            if key not in transaction:
                logger.error("Validasi transaksi gagal: kunci '%s' tidak ditemukan.", key)
                return False

        # Validasi alamat pengirim dan penerima
        if not is_valid_address(transaction["sender"]):
            logger.error("Alamat pengirim tidak valid: %s", transaction["sender"])
            return False
        if not is_valid_address(transaction["recipient"]):
            logger.error("Alamat penerima tidak valid: %s", transaction["recipient"])
            return False

        # Validasi jumlah
        if not isinstance(transaction["amount"], (int, float)) or transaction["amount"] <= 0:
            logger.error("Validasi transaksi gagal: jumlah (%s) tidak valid.", transaction["amount"])
            return False

        # Verifikasi tanda tangan digital menggunakan eth_account
        if not verify_eth_signature(transaction):
            logger.error("Validasi transaksi gagal: tanda tangan digital tidak valid.")
            return False

        return True

    def add_new_transaction(self, transaction: Dict) -> bool:
        """
        Menambahkan transaksi baru ke dalam pool transaksi yang belum dikonfirmasi, setelah validasi.
        Jika transaksi gagal divalidasi, method ini mengembalikan False untuk memberitahu pemanggil.
        
        Args:
            transaction (dict): Transaksi yang akan ditambahkan.
            
        Returns:
            bool: True jika transaksi diterima, False jika ditolak.
        """
        if self.validate_transaction(transaction):
            self.unconfirmed_transactions.append(transaction)
            logger.info("Transaksi berhasil ditambahkan: %s", transaction)
            return True
        else:
            logger.error("Transaksi ditolak: %s", transaction)
            return False

    def proof_of_work(self, block: Block) -> Block:
        """
        Algoritma Proof-of-Work untuk menemukan nonce yang membuat hash blok valid
        berdasarkan difficulty saat ini.
        
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

        # Penyesuaian difficulty secara dinamis
        if mining_time < self.target_mine_time * 0.9:
            self.difficulty += 1
            logger.info("Mining terlalu cepat (%.2f detik). Menaikkan difficulty ke %d.", mining_time, self.difficulty)
        elif mining_time > self.target_mine_time * 1.1 and self.difficulty > 1:
            self.difficulty -= 1
            logger.info("Mining terlalu lambat (%.2f detik). Menurunkan difficulty ke %d.", mining_time, self.difficulty)
        else:
            logger.info("Waktu mining optimal (%.2f detik). Difficulty tetap %d.", mining_time, self.difficulty)

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

# ----------------------- TEST CASES -----------------------

def run_tests():
    """
    Menjalankan test case untuk:
      - Transaksi valid dan tidak valid.
      - Mining dengan difficulty yang berbeda.
      - Percobaan untuk corrupt chain.
    """
    logger.info("=== MEMULAI TEST CASE ===")
    blockchain = Blockchain()

    # Test 1: Transaksi valid
    valid_tx = {
        "sender": "0xAbC1234567890abcdef1234567890ABCDEF1234",
        "recipient": "0xDef9876543210fedcba9876543210FEDCBA9876",
        "amount": 50.0,
        # Contoh tanda tangan Ethereum dummy (hex string)
        "signature": "0x3045022100dff9f1e8c6e4f7f9bd79f3d7a0ad8bcb53b73d0a6cda1a7fbd8c2e3d5a8e1c1e02206a1f1f3c4e3e8c1f2b1d7f3a0ad8bcb53b73d0a6cda1a7fbd8c2e3d5a8e1c1e"
    }
    if blockchain.add_new_transaction(valid_tx):
        logger.info("Test transaksi valid: PASSED")
    else:
        logger.error("Test transaksi valid: GAGAL")

    # Test 2: Transaksi tidak valid (misal, field 'amount' negatif atau alamat tidak valid)
    invalid_tx = {
        "sender": "0xInvalidAddress",
        "recipient": "0xDef9876543210fedcba9876543210FEDCBA9876",
        "amount": -10.0,
        "signature": valid_tx["signature"]
    }
    if not blockchain.add_new_transaction(invalid_tx):
        logger.info("Test transaksi tidak valid: PASSED")
    else:
        logger.error("Test transaksi tidak valid: GAGAL")

    # Test 3: Mining blok dengan transaksi valid (harus ada transaksi di pool)
    mined_block = blockchain.mine()
    if mined_block:
        logger.info("Test mining blok: PASSED")
    else:
        logger.error("Test mining blok: GAGAL")

    # Test 4: Meng-corrupt chain dan memvalidasinya
    if len(blockchain.chain) > 1:
        # Corrupt blok kedua
        blockchain.chain[1]._transactions.append({"sender": "0xEve000000000000000000000000000000000000", 
                                                    "recipient": "0xMallory00000000000000000000000000000000", 
                                                    "amount": 100,
                                                    "signature": valid_tx["signature"]})
        if not blockchain.is_chain_valid():
            logger.info("Test corrupt chain: PASSED")
        else:
            logger.error("Test corrupt chain: GAGAL")
    else:
        logger.info("Tidak ada blok kedua untuk menguji corrupt chain.")

    logger.info("=== TEST CASE SELESAI ===")

if __name__ == '__main__':
    run_tests()
