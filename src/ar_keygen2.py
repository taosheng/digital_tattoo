
import json
import os
import base64
import hashlib
from cryptography.hazmat.primitives.asymmetric import rsa
from arweave.arweave_lib import Wallet  # 導入工具庫進行讀取測試

def int_to_base64url(n):
    """將整數轉換為 Arweave 規格的 Base64URL 字串"""
    b = n.to_bytes((n.bit_length() + 7) // 8, 'big')
    return base64.urlsafe_b64encode(b).decode('utf-8').rstrip('=')

def generate_arweave_jwk():
    """產生符合 Arweave 規格的 RSA-4096 JWK"""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
    numbers = private_key.private_numbers()
    
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
    return jwk

def main():
    print(f"🚀 啟動原生加密引擎並進行 arweave-python-client 相容性測試...\n")
    
    for i in range(1, 3):
        filename = f"ar_new_wallet_{i}.json"
        try:
            # 1. 產生 JWK 內容
            jwk = generate_arweave_jwk()
            
            # 2. 寫入檔案
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(jwk, f, indent=4)
            
            print(f"✅ 檔案 {filename} 已產出。")

            # 3. 關鍵步驟：使用 arweave-python-client 嘗試讀取
            # 只要檔案存在，Wallet(filename) 就不會再噴出 FileNotFoundError
            test_wallet = Wallet(filename)
            
            print(f"🔍 相容性測試成功！")
            print(f"   📍 Arweave 識別地址: {test_wallet.address}")
            print(f"   💾 絕對路徑: {os.path.abspath(filename)}\n")
            
        except Exception as e:
            print(f"❌ 處理錢包 {i} 時發生錯誤: {e}")

if __name__ == "__main__":
    # 確保已安裝: pip install cryptography arweave-python-client
    main()
