import logging

# Konfigurasi logging dasar
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AUTHORIZED_NODES = {
    "http://localhost:5000",
    "http://localhost:5001",
    "http://localhost:5002"
}

def is_authorized(node_address: str) -> bool:
    """
    Cek apakah node terotorisasi untuk menambah blok.

    Args:
        node_address (str): URL atau alamat node.

    Returns:
        bool: True jika node ada dalam daftar node yang terpercaya, False jika tidak.
    """
    return node_address in AUTHORIZED_NODES

def validate_block(block, last_block) -> bool:
    """
    Validasi blok baru berdasarkan blok terakhir dalam chain.

    Pemeriksaan yang dilakukan:
    - Indeks blok harus berturut-turut.
    - Field previous_hash dari blok baru harus sama dengan hash dari blok terakhir.
    - Hash blok baru harus sama dengan hasil kalkulasi ulang berdasarkan kontennya.

    Args:
        block: Objek blok baru yang akan divalidasi.
        last_block: Blok terakhir dari chain saat ini.

    Returns:
        bool: True jika blok valid, False jika tidak.
    """
    # Pastikan block dan last_block tidak None
    if block is None or last_block is None:
        logger.error("Block atau last_block tidak boleh None.")
        return False

    # Validasi indeks blok
    expected_index = last_block.index + 1
    if block.index != expected_index:
        logger.error("Indeks blok tidak valid. Diharapkan %d, tetapi mendapatkan %d", expected_index, block.index)
        return False

    # Validasi previous_hash
    if block.previous_hash != last_block.hash:
        logger.error("Hash previous tidak valid. Diharapkan %s, tetapi mendapatkan %s", last_block.hash, block.previous_hash)
        return False

    # Validasi hash blok dengan menghitung ulang
    calculated_hash = block.calculate_hash()
    if block.hash != calculated_hash:
        logger.error("Hash blok tidak valid. Dihitung %s, tetapi mendapatkan %s", calculated_hash, block.hash)
        return False

    # Jika semua pengecekan lolos, blok dianggap valid
    return True
