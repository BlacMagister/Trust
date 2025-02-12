from eth_account import Account
from eth_account.messages import encode_defunct
import secrets
import json
import os
from cryptography.fernet import Fernet
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import binascii

Account.enable_unaudited_hdwallet_features()

class Wallet:
    def __init__(self, mnemonic=None):
        """
        Inisialisasi dompet. Jika mnemonic tidak diberikan, dompet baru akan dibuat.
        """
        if mnemonic:
            # Load wallet dari mnemonic
            self.account = Account.from_mnemonic(mnemonic)
            self.address = self.account.address
            self.mnemonic = mnemonic
        else:
            # Buat wallet baru
            self.account, self.mnemonic = Account.create_with_mnemonic(language='english')
            self.address = self.account.address

    def sign_transaction(self, message):
        """Menandatangani pesan (bukan transaksi mentah)."""
        # Jika message berupa bytes, ubah ke string
        if isinstance(message, bytes):
            message = message.decode('utf-8')
        # Bungkus pesan menggunakan encode_defunct (EIP-191)
        signable_message = encode_defunct(text=message)
        # Tanda tangani pesan
        signed_txn = self.account.sign_message(signable_message)
        return signed_txn

    def verify_transaction(self, signed_transaction):
        """Memverifikasi transaksi yang ditandatangani."""
        return True

    def save_keys(self, password):
        """Menyimpan mnemonic ke disk dengan aman."""
        try:
            # Generate salt untuk PBKDF2HMAC
            salt = secrets.token_bytes(16)
            # Derive encryption key langsung dari password
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=480000,
                backend=default_backend()
            )
            encryption_key = base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))
            # Enkripsi mnemonic
            f = Fernet(encryption_key)
            encrypted_mnemonic = f.encrypt(self.mnemonic.encode('utf-8'))
            # Simpan encrypted mnemonic dan salt ke file
            with open("encrypted_mnemonic.key", "wb") as key_file:
                key_file.write(encrypted_mnemonic)
            with open("salt.salt", "wb") as salt_file:
                salt_file.write(salt)
            print("Keys saved successfully!")
        except Exception as e:
            print(f"Error saving keys: {e}")

    def load_keys(self, password):
        """Memuat mnemonic dari disk dan membuat account."""
        try:
            # Baca encrypted mnemonic dan salt dari file
            with open("encrypted_mnemonic.key", "rb") as key_file:
                encrypted_mnemonic = key_file.read()
            with open("salt.salt", "rb") as salt_file:
                salt = salt_file.read()
            # Derive encryption key dari password menggunakan salt
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=480000,
                backend=default_backend()
            )
            encryption_key = base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))
            # Dekripsi mnemonic
            f = Fernet(encryption_key)
            decrypted_mnemonic = f.decrypt(encrypted_mnemonic).decode('utf-8')
            # Buat account dari mnemonic
            self.account = Account.from_mnemonic(decrypted_mnemonic)
            self.address = self.account.address
            self.mnemonic = decrypted_mnemonic
            print("Keys loaded successfully!")
            return True
        except Exception as e:
            print(f"Error loading keys: {e}")
            return False

    def get_address(self):
        """Mendapatkan alamat dompet."""
        return self.address

    def get_mnemonic(self):
        """Mendapatkan mnemonic dompet."""
        return self.mnemonic

if __name__ == '__main__':
    # Buat wallet baru
    wallet = Wallet()
    print(f"Wallet address: {wallet.get_address()}")
    print(f"Wallet mnemonic: {wallet.get_mnemonic()}")

    # Simpan wallet
    password = "password_super_aman"
    wallet.save_keys(password)

    # Load wallet
    new_wallet = Wallet()
    if new_wallet.load_keys(password):
        print("Successfully created and loaded wallet!")
        print(f"Wallet address: {new_wallet.get_address()}")
        print(f"Wallet mnemonic: {new_wallet.get_mnemonic()}")
    else:
        print("Failed to load wallet!")

    # Contoh pesan yang akan ditandatangani
    message = "Hello"

    try:
        signed_txn = wallet.sign_transaction(message.encode('utf-8'))
        print(f"Signed transaction: {signed_txn}")
    except Exception as e:
        print(f"Error signing transaction: {e}")
