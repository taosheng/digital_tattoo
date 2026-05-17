
import json
import os
import base64
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

def int_to_base64url(n):
    """將整數轉換為 Base64URL 編碼格式（JWK 標準）"""
    # 轉換為位元組，使用 big-endian
    b = n.to_bytes((n.bit_length() + 7) // 8, 'big')
    # 編碼並移除 padding (=)
    return base64.urlsafe_b64encode(b).decode('utf-8').rstrip('=')

def generate_arweave_jwk(filename):
    """手動產生符合 Arweave 規格的 RSA-4096 JWK 錢包"""
    # 1. 產生 RSA 私鑰
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096
    )
    
    # 2. 取得 RSA 參數
    numbers = private_key.private_numbers()
    
    # 3. 建立 JWK 字典
    # 這些欄位是 Arweave 識別錢包的標準規格
    jwk = {
        "kty": "RSA",
        "n": int_to_base64url(numbers.public_numbers.n),
        "e": int_to_base64url(numbers.public_numbers.e),
        "d": int_to_base64url(numbers.d),
        "p": int_to_base64url(numbers.p),
        "q": int_to_base64url(numbers.q),
        "dp": int_to_base64url(numbers.dmp1),
        "dq": int_to_base64url(numbers.dmq1),
        "qi": int_to_base64url(numbers.iqmp)
    }

    # 4. 儲存檔案
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(jwk, f, indent=4)
    
    return jwk

def get_arweave_address(jwk):
    """從 JWK 產出 Arweave 地址 (SHA-256 of 'n')"""
    import hashlib
    n_bytes = base64.urlsafe_b64decode(jwk['n'] + '==')
    sha256 = hashlib.sha256(n_bytes).digest()
    return base64.urlsafe_b64encode(sha256).decode('utf-8').rstrip('=')

def main():
    print(f"🚀 啟動原生加密引擎，產生 Arweave 錢包...\n")
    
    for i in range(1, 3):
        filename = f"ar_wallet_{i}.json"
        try:
            jwk = generate_arweave_jwk(filename)
            address = get_arweave_address(jwk)
            
            print(f"✅ 錢包 {i} 建立成功！")
            print(f"   📍 地址: {address}")
            print(f"   💾 檔案: {os.path.abspath(filename)}\n")
        except Exception as e:
            print(f"❌ 發生錯誤: {e}")

if __name__ == "__main__":
    main()
