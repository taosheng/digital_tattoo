# (a) 帳號產生器 (`keygen.py`)
#執行這個程式來產生測試用的帳號。請記得去 [Solana Faucet](https://faucet.solana.com/) 貼上發送者的地址領取測試幣。

from solders.keypair import Keypair

# 產生發送者 A
sender = Keypair()
# 產生接收者 B
receiver = Keypair()

print(f"--- 帳號 A (發送者) ---")
print(f"地址 (Public Key): {sender.pubkey()}")
print(f"私鑰 (Secret Key): {list(sender.to_bytes())}")
print(f"\n--- 帳號 B (接收者) ---")
print(f"地址 (Public Key): {receiver.pubkey()}")
print(f"\n請將上述資訊填入 .env 檔案中")
