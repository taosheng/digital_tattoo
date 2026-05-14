import secrets
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

def generate_aes_key() -> str:
    """Generate 16 raw bytes (128-bit entropy) and represent as 32-character hex string."""
    return secrets.token_hex(16)

def encrypt_data(data: bytes, key: bytes) -> bytes:
    """Encrypts data using AES CBC mode and returns IV + Ciphertext."""
    cipher = AES.new(key, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(data, AES.block_size))
    return cipher.iv + ct_bytes

def decrypt_data(encrypted_data: bytes, key: bytes) -> bytes:
    """Decrypts data using AES CBC mode from IV + Ciphertext."""
    iv = encrypted_data[:16]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(encrypted_data[16:]), AES.block_size)
