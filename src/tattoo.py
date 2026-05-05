
import os
import base64
import math
import ast
import argparse
import time
from dotenv import load_dotenv

# Solana 相關套件
from solana.rpc.api import Client
from solders.transaction import Transaction
from solders.message import Message
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import transfer, TransferParams
from solders.instruction import Instruction

# 載入環境變數
load_dotenv()

# 設定連線與固定程序 ID
RPC_URL = "https://api.devnet.solana.com"
client = Client(RPC_URL)
# SPL Memo Program 官方固定地址
MEMO_PROGRAM_ID = Pubkey.from_string("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr")

# 從 .env 讀取金鑰配置
try:
    sender_key = Keypair.from_bytes(bytes(ast.literal_eval(os.getenv("SENDER_SECRET_KEY"))))
    receiver_pub = Pubkey.from_string(os.getenv("RECEIVER_PUBLIC_KEY"))
except Exception as e:
    print(f"錯誤：無法從 .env 讀取正確的金鑰資訊。請確認格式正確。{e}")
    exit(1)

def upload(file_path, tattoo_id):
    if not os.path.exists(file_path):
        print(f"錯誤：找不到檔案 {file_path}")
        return

    with open(file_path, "rb") as f:
        raw_data = base64.b64encode(f.read()).decode('utf-8')
    
    # 每筆交易 Memo 限制，預留標籤空間
    chunk_size = 800 
    total_chunks = math.ceil(len(raw_data) / chunk_size)
    print(f"啟動刺青程序... ID: {tattoo_id}, 預計發送 {total_chunks} 筆交易")

    for i in range(total_chunks):
        chunk = raw_data[i*chunk_size : (i+1)*chunk_size]
        # 結構化標籤：TATTOO:ID|目前序號|總數|資料
        memo_data = f"TATTOO:{tattoo_id}|{i+1}|{total_chunks}|{chunk}"
        
        # 獲取最新區塊雜湊 (Blockhash)
        recent_blockhash = client.get_latest_blockhash().value.blockhash
        
        # 指令 1: 微額轉帳作為交易載體
        ix_transfer = transfer(TransferParams(
            from_pubkey=sender_key.pubkey(), 
            to_pubkey=receiver_pub, 
            lamports=1000
        ))
        
        # 指令 2: 寫入數位刺青內容
        ix_memo = Instruction(
            program_id=MEMO_PROGRAM_ID, 
            data=bytes(memo_data, 'utf-8'), 
            accounts=[]
        )
        
        # 建立交易訊息並簽署
        msg = Message([ix_transfer, ix_memo], sender_key.pubkey())
        txn = Transaction([sender_key], msg, recent_blockhash)
        
        try:
            res = client.send_transaction(txn)
            print(f"進度 ({i+1}/{total_chunks}): {res.value}")
            # 為避免 RPC 頻率限制，間隔 0.5 秒
            time.sleep(0.5)
        except Exception as e:
            print(f"發送第 {i+1} 筆失敗: {e}")

    print(f"\n刺青完成！唯一編號為: {tattoo_id}")

def download(tattoo_id, output_path):
    print(f"正在區塊鏈上搜尋刺青 ID: {tattoo_id}...")
    # 取得接收者帳號的所有交易紀錄
    signatures = client.get_signatures_for_address(receiver_pub).value
    chunks = {}
    total_needed = 0

    for sig_info in signatures:
        # 取得單筆交易詳細內容
        tx_res = client.get_transaction(sig_info.signature, max_supported_transaction_version=0).value
        if not tx_res: continue
        
        logs = tx_res.transaction.meta.log_messages
        for log in logs:
            # 從 Program log 中解析 Memo 內容
            if "Program log: Memo" in log:
                # 簡單字串處理取得標籤後內容
                try:
                    content = log.split("Memo (len ")[1].split("): ")[1].strip('"')
                    if content.startswith(f"TATTOO:{tattoo_id}|"):
                        parts = content.split("|")
                        idx = int(parts[1])
                        total_needed = int(parts[2])
                        chunks[idx] = parts[3]
                        print(f"找到分片: {idx}/{total_needed}")
                except:
                    continue

    if total_needed > 0 and len(chunks) == total_needed:
        # 依照序號排序並重組
        full_b64 = "".join([chunks[i] for i in sorted(chunks.keys())])
        with open(output_path, "wb") as f:
            f.write(base64.b64decode(full_b64))
        print(f"\n檔案重組成功！已存至: {output_path}")
    else:
        print(f"\n資料不完整。需要 {total_needed} 片，僅找到 {len(chunks)} 片。")

def list_tattoos():
    print(f"正在掃描帳號 {receiver_pub} 的刺青紀錄...")
    signatures = client.get_signatures_for_address(receiver_pub).value
    found_ids = set()
    
    for sig_info in signatures:
        tx_res = client.get_transaction(sig_info.signature, max_supported_transaction_version=0).value
        if not tx_res: continue
        
        for log in tx_res.transaction.meta.log_messages:
            if "TATTOO:" in log:
                try:
                    tattoo_id = log.split("TATTOO:")[1].split("|")[0]
                    found_ids.add(tattoo_id)
                except:
                    continue
    
    if found_ids:
        print(f"目前鏈上發現的刺青清單: {list(found_ids)}")
    else:
        print("目前該地址沒有任何刺青紀錄。")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Solana Digital Tattoo Tool")
    parser.add_argument("action", choices=["upload", "download", "list"], help="執行動作")
    parser.add_argument("--file", help="檔案路徑 (上傳或下載存檔)")
    parser.add_argument("--id", help="刺青唯一編號")
    args = parser.parse_args()

    if args.action == "upload":
        if not args.file or not args.id:
            print("上傳需要提供 --file 與 --id")
        else:
            upload(args.file, args.id)
    elif args.action == "download":
        if not args.file or not args.id:
            print("下載需要提供 --file 與 --id")
        else:
            download(args.id, args.file)
    elif args.action == "list":
        list_tattoos()
