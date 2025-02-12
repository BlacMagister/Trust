from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import os
import bcrypt # Untuk hashing password
from cryptography.hazmat.primitives import kdf # Untuk Key Derivation Function
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class Wallet:
    def __init__(self):
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()
        self.salt = bcrypt.gensalt() # Generate salt unik untuk setiap wallet
        self.encryption_key = None # Encryption key akan di-generate saat save_keys

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
        """Menyimpan key ke disk dengan aman (dienkripsi dan password di-hash)."""

        # 1. Hash password dengan bcrypt + salt
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), self.salt)

        # 2. Generate encryption key dari hashed password menggunakan KDF (PBKDF2HMAC)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32, # Panjang key AES-256
            salt=self.salt, # Pake salt yang sama
            iterations=480000, # Iterasi yang disarankan
            backend=default_backend()
        )
        self.encryption_key = base64.urlsafe_b64encode(kdf.derive(hashed_password))

        # 3. Enkripsi private key
        private_key_pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')

        f = Fernet(self.encryption_key)
        encrypted_private_key = f.encrypt(private_key_pem.encode('utf-8'))

        # 4. Simpan encrypted private key dan salt ke file (PASTIKAN AMAN!)
        with open("encrypted_private_key.key", "wb") as key_file:
            key_file.write(encrypted_private_key)
        with open("salt.salt", "wb") as salt_file:
            salt_file.write(self.salt)

    def load_keys(self, password):
        """Memuat key dari disk (mendekripsi dan verifikasi password)."""
        try:
            with open("encrypted_private_key.key", "rb") as key_file:
                encrypted_private_key = key_file.read()

            with open("salt.salt", "rb") as salt_file:
                self.salt = salt_file.read()

            # 1. Hash password yang diinput
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), self.salt)

            # 2. Generate encryption key dari hashed password menggunakan KDF
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32, # Panjang key AES-256
                salt=self.salt,
                iterations=480000,
                backend=default_backend()
            )
            encryption_key = base64.urlsafe_b64encode(kdf.derive(hashed_password))

            # 3. Dekripsi private key
            f = Fernet(encryption_key)
            decrypted_private_key = f.decrypt(encrypted_private_key).decode('utf-8')

            # 4. Load private key
            self.private_key = serialization.load_pem_private_key(
                decrypted_private_key.encode('utf-8'),
                password=None,
                backend=default_backend()
            )
            self.public_key = self.private_key.public_key()
        except Exception as e:
            print(f"Error loading keys: {e}")
            return False #Indikasi gagal load keys
        return True #Indikasi berhasil load keys

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

    password = "password_super_aman" # Gantilah dengan password yang kuat!
    wallet.save_keys(password)

    new_wallet = Wallet()
    if new_wallet.load_keys(password):
        print("Successfully created and loaded wallet!")
    else:
        print("Failed to load wallet!")
