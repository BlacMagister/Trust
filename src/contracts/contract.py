import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class SmartContract:
    """
    Representasi smart contract dengan storage internal.
    
    Atribut:
      - contract_address: Alamat unik kontrak.
      - owner_address: Alamat pemilik kontrak.
      - code: Kode kontrak (misalnya sebagai string kode Python untuk dieksekusi secara dinamis).
      - storage: Dictionary untuk menyimpan state kontrak.
    """
    
    def __init__(self, contract_address: str, owner_address: str, code: str) -> None:
        """
        Inisialisasi smart contract.
        
        Args:
            contract_address (str): Alamat unik kontrak.
            owner_address (str): Alamat pemilik kontrak.
            code (str): Kode kontrak sebagai string.
        """
        self.contract_address: str = contract_address
        self.owner_address: str = owner_address
        self.code: str = code
        self.storage: Dict[str, Any] = {}  # Tempat penyimpanan state kontrak

    def execute(self, transaction: Dict[str, Any], blockchain: Any) -> bool:
        """
        Eksekusi smart contract dengan melakukan interpretasi kode kontrak.
        
        Proses:
          - Menyiapkan environment terbatas yang hanya mengizinkan akses ke variabel yang diperlukan.
          - Mengeksekusi kode kontrak dengan parameter 'transaction', 'blockchain', dan 'contract' (self).
          - Menangani error eksekusi dan mengembalikan status eksekusi.
          
        Args:
            transaction (dict): Transaksi yang memicu eksekusi kontrak.
            blockchain (Any): Referensi ke instance blockchain (untuk akses state global jika diperlukan).
        
        Returns:
            bool: True jika eksekusi berhasil, False jika terjadi error.
        """
        logger.info("Executing contract %s triggered by transaction %s", self.contract_address, transaction)
        
        # Environment terbatas untuk eksekusi kontrak
        exec_env = {
            "transaction": transaction,
            "blockchain": blockchain,
            "contract": self,
            "__builtins__": {}  # Membatasi builtins untuk alasan keamanan; perlu penyesuaian sesuai kebutuhan
        }
        
        try:
            # Perlu diingat: penggunaan exec() memiliki risiko keamanan.
            exec(self.code, exec_env)
            logger.info("Execution of contract %s succeeded.", self.contract_address)
            return True
        except Exception as e:
            logger.error("Execution of contract %s failed: %s", self.contract_address, str(e))
            return False

    def get_storage(self, key: str) -> Any:
        """
        Mengembalikan nilai yang tersimpan di storage berdasarkan key.
        
        Args:
            key (str): Kunci penyimpanan.
            
        Returns:
            Any: Nilai yang tersimpan, atau None jika key tidak ditemukan.
        """
        value = self.storage.get(key)
        logger.debug("Get storage key '%s': %s", key, value)
        return value

    def set_storage(self, key: str, value: Any) -> None:
        """
        Menyimpan atau memperbarui nilai di storage kontrak.
        
        Args:
            key (str): Kunci penyimpanan.
            value (Any): Nilai yang akan disimpan.
        """
        self.storage[key] = value
        logger.debug("Set storage key '%s' to value: %s", key, value)

    def __repr__(self) -> str:
        return f"<SmartContract address={self.contract_address} owner={self.owner_address}>"

    def __str__(self) -> str:
        return f"SmartContract({self.contract_address}) owned by {self.owner_address}, Storage: {self.storage}"
