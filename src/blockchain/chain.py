from src.blockchain.block import Block, create_genesis_block
import time

class Blockchain:
    def __init__(self):
        self.chain = [create_genesis_block()]

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

    def __repr__(self):
        return f"Blockchain with {len(self.chain)} blocks. Valid: {self.is_chain_valid()}"

if __name__ == '__main__':
    blockchain = Blockchain()
    new_block = Block(1, time.time(), ["transaksi 1", "transaksi 2"], blockchain.chain[-1].hash)
    blockchain.add_block(new_block)

    new_block_2 = Block(2, time.time(), ["transaksi 3", "transaksi 4"], blockchain.chain[-1].hash)
    blockchain.add_block(new_block_2)
    print(blockchain)

    print(f"Blockchain valid? {blockchain.is_chain_valid()}")
