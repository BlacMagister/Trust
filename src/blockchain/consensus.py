AUTHORIZED_NODES = {"http://localhost:5000"}  # Contoh: ganti dengan daftar node yang terpercaya

def is_authorized(node_address):
    """
    Cek apakah node terotorisasi buat nambah blok.
    """
    return node_address in AUTHORIZED_NODES

def validate_block(block, last_block):
    """
    Validasi blok baru.
    """
    # Pastikan index blok bener
    if block.index != last_block.index + 1:
        print("Invalid block index")
        return False

    # Pastikan hash previous_hash bener
    if block.previous_hash != last_block.hash:
        print("Invalid previous hash")
        return False

    # Pastikan hash blok bener
    if block.hash != block.calculate_hash():
        print("Invalid block hash")
        return False

    return True
