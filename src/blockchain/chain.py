from src.blockchain.block import Block, create_genesis_block
import time
from src.blockchain.consensus import is_authorized, validate_block
import os
import json
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import secrets

class Blockchain:
    def __init__(self):
        self.chain = [create_genesis_block()]
        self.unconfirmed_transactions = []

    def add_new_transaction(self, transaction):
        self.unconfirmed_transactions.append(transaction)

    def mine(self):
        """
        Fungsi buat nambang blok baru.
        """
        if not self.unconfirmed_transactions:
            return False

        last_block = self.chain[-1]

        new_block = Block(
            index=last_block.index + 1,
            timestamp=time.time(),
            transactions=self.unconfirmed_transactions,
            previous_hash=last_block.hash,
            nonce=secrets.randbelow(100)  # Angka random buat bukti kerja
        )

        # Validasi blok
        if validate_block(new_block, last_block):
            self.chain.append(new_block)
            self.unconfirmed_transactions = []
            return new_block
        else:
            return False

    def add_block(self, block):
        """Menambahkan blok baru ke rantai."""
        block.previous_hash = self.chain[-1].hash
        block.hash = block.calculate_hash()
        self.chain.append(block)

    def is_chain_valid(self):
        """Memvalidasi integritas rantai."""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i-1]

            if current_block.hash != current_block.calculate_hash():
                return False

            if current_block.previous_hash != previous_block.hash:
                return False

        return True

    @property
    def last_block(self):
        return self.chain[-1]

    def is_valid_block(self, block, last_block):
        return validate_block(block, last_block)

    def __repr__(self):
        return f"Blockchain with {len(self.chain)} blocks. Valid: {self.is_chain_valid()}"
