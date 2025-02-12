from eth_account import Account
Account.enable_unaudited_hdwallet_features()
import secrets
import json
import os
from cryptography.fernet import Fernet
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import bcrypt

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

    def sign_transaction(self, transaction):
        """Menandatangani transaksi."""
        signed_txn = self.account.sign_transaction(transaction)
        return signed_txn

    def verify_transaction(self, signed_transaction):
        """Memverifikasi transaksi yang ditandatangani."""
        # Implementasi verifikasi transaksi di sini (tergantung blockchain yang digunakan)
        return True

    def save_keys(self, password):
        """Menyimpan mnemonic ke disk dengan aman."""
        try:
            # 1. Hash password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

            # 2. Generate salt untuk PBKDF2HMAC
            salt = secrets.token_bytes(16)

            # 3. Generate encryption key dari hashed password menggunakan PBKDF2HMAC
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=480000,
                backend=default_backend()
            )
            encryption_key = base64.urlsafe_b64encode(kdf.derive(hashed_password))

            # 4. Enkripsi mnemonic
            f = Fernet(encryption_key)
            encrypted_mnemonic = f.encrypt(self.mnemonic.encode('utf-8'))

            # 5. Simpan encrypted mnemonic dan salt ke file
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
            # 1. Baca encrypted mnemonic dan salt dari file
            with open("encrypted_mnemonic.key", "rb") as key_file:
                encrypted_mnemonic = key_file.read()
            with open("salt.salt", "rb") as salt_file:
                salt = salt_file.read()

            # 2. Hash password
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

            # 3. Generate encryption key dari hashed password menggunakan PBKDF2HMAC
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=480000,
                backend=default_backend()
            )
            encryption_key = base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))

            # 4. Dekripsi mnemonic
            f = Fernet(encryption_key)
            decrypted_mnemonic = f.decrypt(encrypted_mnemonic).decode('utf-8')

            # 5. Buat account dari mnemonic
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

    # Contoh transaksi (DIUBAH)
    transaction = {
        'to': '0xd3CdA947B93c4E1CD4989DD08eAB4Cc9984F',  # Alamat tujuan
        'value': 1000000000,  # Nilai transaksi (dalam Wei)
        'gas': 21000,  # Batas gas
        'gasPrice': 1000000000  # Harga gas
    }

    try:
        signed_txn = wallet.sign_transaction(transaction)
        print(f"Signed transaction: {signed_txn}")
    except Exception as e:
        print(f"Error signing transaction: {e}")
