import unittest
from src.blockchain.block import Block

class TestBlock(unittest.TestCase):

    def test_calculate_hash(self):
        block = Block(0, 1678886400, ["transaction1"], "previous_hash")
        self.assertIsInstance(block.calculate_hash(), str)
        self.assertEqual(len(block.calculate_hash()), 64)

    # Tambahin test case lain di sini

if __name__ == '__main__':
    unittest.main()
