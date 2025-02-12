def is_authorized(public_key):
    """Memeriksa apakah public key terotorisasi."""
    # Implementasi PoA yang sebenarnya di sini
    return True

def validate_block(block):
    """Memvalidasi blok."""
    # Implementasi validasi blok di sini
    if not block.transactions:
        return False
    return True
