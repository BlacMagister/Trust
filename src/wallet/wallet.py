from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import os

class Wallet:
    def __init__(self):
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()
        self.encryption_key = Fernet.generate_key() # Untuk enkripsi key saat disimpan

    def sign_transaction(self, transaction_data):
        """Menandatangani data transaksi dengan private key."""
        message = transaction_data.encode('utf-8')
        signature = self.private_key.sign(
            message,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature

    def verify_signature(self, signature, transaction_data, public_key):
        """Memverifikasi tanda tangan dengan public key."""
        message = transaction_data.encode('utf-8')
        try:
            public_key.verify(
                signature,
                message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except:
            return False

    def save_keys(self, password):
        """Menyimpan key ke disk dengan aman (dienkripsi)."""
        private_key_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()  # Bisa diganti dengan enkripsi password-based
        ).decode('utf-8')

        f = Fernet(self.encryption_key)
        encrypted_private_key = f.encrypt(private_key_pem.encode('utf-8'))

        # Simpan encrypted_private_key dan encryption_key ke file (pastikan aman)
        with open("encrypted_private_key.key", "wb") as key_file:
            key_file.write(encrypted_private_key)
        with open("encryption.key", "wb") as encryption_key_file:
            encryption_key_file.write(self.encryption_key)

    def load_keys(self, password):
        """Memuat key dari disk (mendekripsi)."""
        with open("encrypted_private_key.key", "rb") as key_file:
            encrypted_private_key = key_file.read()

        with open("encryption.key", "rb") as encryption_key_file:
            self.encryption_key = encryption_key_file.read()

        f = Fernet(self.encryption_key)
        decrypted_private_key = f.decrypt(encrypted_private_key).decode('utf-8')

        self.private_key = serialization.load_pem_private_key(
            decrypted_private_key.encode('utf-8'),
            password=None,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()

def wallet_to_string(wallet):
    """Mengubah public key wallet menjadi string yang bisa dibaca."""
    public_key = wallet.public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')
    return public_key

if __name__ == '__main__':
    wallet = Wallet()
    transaction_data = "Transfer 10 CHK ke Budi"
    signature = wallet.sign_transaction(transaction_data)

    public_key = wallet.public_key
    is_valid = wallet.verify_signature(signature, transaction_data, public_key)

    print(f"Signature valid? {is_valid}")
    print(f"Wallet public key: \n {wallet_to_string(wallet)}")

    wallet.save_keys("password_aman")
    new_wallet = Wallet()
    new_wallet.load_keys("password_aman")

    print("Successfully create and load wallet!")
