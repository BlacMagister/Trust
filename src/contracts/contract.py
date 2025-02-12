class SmartContract:
    def __init__(self, contract_address, owner_address, code):
        self.contract_address = contract_address
        self.owner_address = owner_address
        self.code = code
        self.storage = {}  # Tempat nyimpen data contract

    def execute(self, transaction, blockchain):
        """Eksekusi smart contract."""
        # Logika eksekusi contract ada di sini (interpretasi self.code)
        # Ini contoh sederhana, implementasi yang beneran lebih kompleks
        print(f"Executing contract {self.contract_address}...")

        # Example, just transfer something
        return True

    def get_storage(self, key):
        """Mendapatkan data dari storage contract."""
        return self.storage.get(key)

    def set_storage(self, key, value):
        """Menyimpan data ke storage contract."""
        self.storage[key] = value
