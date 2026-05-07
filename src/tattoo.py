import os
import base64
import math
import ast
import argparse
import time
import json
from dotenv import load_dotenv

from solana.rpc.api import Client
from solders.transaction import Transaction
from solders.message import Message
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.system_program import transfer, TransferParams
from solders.instruction import Instruction

load_dotenv()

RPC_URL = "https://api.devnet.solana.com"
client = Client(RPC_URL)
MEMO_PROGRAM_ID = Pubkey.from_string("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr")

try:
    sender_key = Keypair.from_bytes(bytes(ast.literal_eval(os.getenv("SENDER_SECRET_KEY"))))
    receiver_pub = Pubkey.from_string(os.getenv("RECEIVER_PUBLIC_KEY"))
except Exception as e:
    print(f"Error: Could not read valid keys from .env. Please check the format. {e}")
    exit(1)

MAX_UPLOAD_SIZE_KB = int(os.getenv("MAX_UPLOAD_SIZE_KB", "1024"))

def check_balances():
    try:
        sender_bal = client.get_balance(sender_key.pubkey()).value
        receiver_bal = client.get_balance(receiver_pub).value
        print(f"[Balance Status] Sender: {sender_bal / 1e9:.6f} SOL, Receiver: {receiver_bal / 1e9:.6f} SOL")
        
        # Minimum rent-exempt balance for a 0-byte account is approx 0.00089088 SOL (890880 lamports)
        if receiver_bal < 890880:
            print("⚠️ Warning: Receiver account balance is too low to pass rent-exempt check. Please airdrop or transfer some SOL to the receiver.")
    except Exception as e:
        print(f"Could not fetch balance: {e}")

def get_tx_with_retry(signature, retries=6):
    """Transaction query with retry mechanism to avoid Solana free node rate limits (429 Too Many Requests)"""
    for attempt in range(retries):
        try:
            # Add delay to avoid hitting limits immediately
            time.sleep(0.5)
            return client.get_transaction(signature, max_supported_transaction_version=0).value
        except Exception as e:
            err_msg = str(e)
            if attempt < retries - 1:
                wait_time = 2.0 ** attempt
                print(f"⚠️ Error querying tx {signature}: {err_msg[:150]}... waiting {wait_time:.1f}s before retrying... ({attempt+1}/{retries})")
                time.sleep(wait_time)
            else:
                print(f"❌ Failed to fetch tx {signature} after {retries} attempts.")
                raise e
    return None

def send_memo_tx(memo_data, current_idx, total, max_retries=5):
    import random
    
    for attempt in range(max_retries):
        try:
            recent_blockhash = client.get_latest_blockhash().value.blockhash
            
            # Add Compute Unit limit instruction (600,000 CUs)
            ix_cu = Instruction(
                program_id=Pubkey.from_string("ComputeBudget111111111111111111111111111111"),
                data=bytes([2]) + (600000).to_bytes(4, 'little'),
                accounts=[]
            )
            
            ix_transfer = transfer(TransferParams(
                from_pubkey=sender_key.pubkey(), 
                to_pubkey=receiver_pub, 
                lamports=1000
            ))
            
            ix_memo = Instruction(
                program_id=MEMO_PROGRAM_ID, 
                data=bytes(memo_data, 'utf-8'), 
                accounts=[]
            )
            
            txn = Transaction.new_signed_with_payer(
                [ix_cu, ix_transfer, ix_memo],
                sender_key.pubkey(),
                [sender_key],
                recent_blockhash
            )
            
            res = client.send_raw_transaction(bytes(txn))
            sig = res.value
            print(f"Progress ({current_idx}/{total}): Sent {sig}")
            
            # Confirm transaction to ensure it actually landed on the blockchain
            confirm_res = client.confirm_transaction(sig)
            if confirm_res.value[0].err:
                raise Exception(f"Transaction failed on-chain: {confirm_res.value[0].err}")
            
            print(f"Progress ({current_idx}/{total}): Confirmed {sig}")
            time.sleep(0.5)
            return str(sig)
        except Exception as e:
            print(f"Attempt {attempt+1}/{max_retries} failed for chunk {current_idx}: {e}")
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2 + random.uniform(0, 2)
                print(f"Retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)
            else:
                print(f"Failed to send or confirm chunk index {current_idx} after {max_retries} attempts")
                return None

def upload(file_path, tattoo_id, user_email):
    if not os.path.exists(file_path):
        print(f"Error: File not found {file_path}")
        return

    file_size = os.path.getsize(file_path)
    if file_size > MAX_UPLOAD_SIZE_KB * 1024:
        print(f"Error: File size ({file_size / 1024:.2f} KB) exceeds the configured limit of {MAX_UPLOAD_SIZE_KB} KB.")
        return

    with open(file_path, "rb") as f:
        raw_data = base64.b64encode(f.read()).decode('utf-8')
    
    chunk_size = 800 
    total_data_chunks = math.ceil(len(raw_data) / chunk_size)
    print(f"Starting file tattoo process... ID: {tattoo_id}, Email: {user_email}, Expected transactions: {total_data_chunks + 1}")

    # index 0: metadata
    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    metadata_dict = {"name": file_name, "size": file_size}
    meta_str = json.dumps(metadata_dict)
    meta_b64 = base64.b64encode(meta_str.encode('utf-8')).decode('utf-8')
    
    signatures = []
    
    # Send Index 0
    memo_data_0 = f"TAO:{user_email}:{tattoo_id}|f|0|{total_data_chunks}|{meta_b64}"
    sig0 = send_memo_tx(memo_data_0, 0, total_data_chunks)
    if not sig0:
        raise Exception("Failed to confirm metadata chunk (index 0). Upload aborted.")
    signatures.append(sig0)

    # Send Index 1 to total_data_chunks
    for i in range(total_data_chunks):
        chunk = raw_data[i*chunk_size : (i+1)*chunk_size]
        memo_data = f"TAO:{user_email}:{tattoo_id}|f|{i+1}|{total_data_chunks}|{chunk}"
        sig = send_memo_tx(memo_data, i+1, total_data_chunks)
        if not sig:
            raise Exception(f"Failed to confirm chunk {i+1}. Upload aborted.")
        signatures.append(sig)

    print(f"\nFile tattoo completed! Unique ID: {tattoo_id}")
    return signatures

def upload_string(text, tattoo_id, user_email):
    if len(text) > 500:
        print("Error: String length exceeds limit (500 characters)")
        return []
        
    raw_data = base64.b64encode(text.encode('utf-8')).decode('utf-8')
    chunk_size = 800 
    total_chunks = math.ceil(len(raw_data) / chunk_size)
    print(f"Starting string tattoo process... ID: {tattoo_id}, Email: {user_email}, Expected transactions: {total_chunks}")

    signatures = []
    for i in range(total_chunks):
        chunk = raw_data[i*chunk_size : (i+1)*chunk_size]
        memo_data = f"TAO:{user_email}:{tattoo_id}|s|{i+1}|{total_chunks}|{chunk}"
        sig = send_memo_tx(memo_data, i+1, total_chunks)
        if not sig:
            raise Exception(f"Failed to confirm string chunk {i+1}. Upload aborted.")
        signatures.append(sig)

    print(f"\nString tattoo completed! Unique ID: {tattoo_id}")
    return signatures

def download(tattoo_id, output_path, user_email):
    print(f"Searching for tattoo ID on blockchain: {tattoo_id} with Email: {user_email}...")
    signatures = client.get_signatures_for_address(receiver_pub).value
    chunks = {}
    total_needed = 0

    for sig_info in signatures:
        tx_res = get_tx_with_retry(sig_info.signature)
        if not tx_res: continue
        
        logs = tx_res.transaction.meta.log_messages
        for log in logs:
            if "Program log: Memo" in log:
                try:
                    content = log.split("Memo (len ")[1].split("): ")[1].strip('"')
                    if content.startswith("TAO:"):
                        parts = content.split("|")
                        tao_head = parts[0].split("TAO:")[1].split(":", 1)
                        if len(tao_head) == 2:
                            t_email, t_id = tao_head[0], tao_head[1]
                        else:
                            t_email, t_id = None, tao_head[0]
                        
                        if t_email and t_email != user_email:
                            continue
                            
                        if t_id == tattoo_id:
                            idx = int(parts[2])
                            total_n = int(parts[3])
                            chunks[idx] = parts[4]
                            total_needed = total_n
                            print(f"Found chunk: {idx}/{total_needed}")
                            
                    elif content.startswith(f"TATTOO:{tattoo_id}|"):
                        parts = content.split("|")
                        idx = int(parts[1])
                        total_needed = int(parts[2])
                        chunks[idx] = parts[3]
                        print(f"Found legacy chunk: {idx}/{total_needed}")
                except:
                    continue

    if total_needed > 0:
        valid = True
        for i in range(1, total_needed + 1):
            if i not in chunks:
                valid = False
                break
        
        if valid:
            full_b64 = "".join([chunks[i] for i in range(1, total_needed + 1)])
            
            # If output_path is provided, write to file, else just print to console
            if output_path:
                with open(output_path, "wb") as f:
                    f.write(base64.b64decode(full_b64))
                print(f"\nFile reconstruction successful! Saved to: {output_path}")
                return True
            else:
                try:
                    text = base64.b64decode(full_b64).decode('utf-8')
                    print(f"\n--- 刺青內容 (Tattoo Content) ---\n{text}\n--------------------------------")
                    return text
                except Exception as e:
                    print("\n⚠️ Data retrieved, but could not be decoded as a UTF-8 String.")
                    return None
            
            if 0 in chunks:
                try:
                    meta_decoded = base64.b64decode(chunks[0]).decode('utf-8')
                    meta_dict = json.loads(meta_decoded)
                    print(f"Parsed original file metadata: {meta_dict}")
                except:
                    print("Could not parse file metadata (Index 0).")
        else:
            print(f"\nIncomplete data. Need chunks 1~{total_needed}, currently missing parts.")
    else:
        print("\nNo data found for this ID.")

def download_by_signatures(signatures):
    from solders.signature import Signature
    chunks = {}
    total_needed = 0
    errors = []
    
    for sig_str in signatures:
        try:
            sig_obj = Signature.from_string(sig_str)
            tx_res = get_tx_with_retry(sig_obj)
            if not tx_res:
                errors.append(f"Transaction {sig_str} returned empty.")
                continue
            
            logs = tx_res.transaction.meta.log_messages
            for log in logs:
                if "Program log: Memo" in log:
                    try:
                        content = log.split("Memo (len ")[1].split("): ")[1].strip('"')
                        if content.startswith("TAO:"):
                            parts = content.split("|")
                            idx = int(parts[2])
                            total_n = int(parts[3])
                            chunks[idx] = parts[4]
                            total_needed = total_n
                    except Exception:
                        pass
        except Exception as e:
            print(f"Error fetching signature {sig_str}: {e}")
            errors.append(f"Sig {sig_str}: {str(e)}")
            continue

    if total_needed > 0 and len(chunks) == total_needed:
        full_b64 = "".join([chunks[i] for i in range(1, total_needed + 1)])
        try:
            return base64.b64decode(full_b64).decode('utf-8')
        except Exception as e:
            raise Exception(f"Failed to decode base64: {str(e)}")
            
    # If we get here, it means we failed to assemble the chunks
    if errors:
        raise Exception("Failed to fetch some signatures from Solana RPC:\n" + "\n".join(errors))
    else:
        raise Exception(f"Incomplete data. Found {len(chunks)} chunks, needed {total_needed}.")

def list_tattoos(user_email=None):
    print(f"Scanning tattoo records for account {receiver_pub}...")
    if user_email:
        print(f"Filter condition Email: {user_email}")
        
    signatures = client.get_signatures_for_address(receiver_pub).value
    tattoos = {}
    
    for sig_info in signatures:
        tx_res = get_tx_with_retry(sig_info.signature)
        if not tx_res: continue
        
        for log in tx_res.transaction.meta.log_messages:
            if "Program log: Memo" in log:
                try:
                    content = log.split("Memo (len ")[1].split("): ")[1].strip('"')
                    if content.startswith("TAO:"):
                        parts = content.split("TAO:")[1].split("|")
                        tao_head = parts[0].split(":", 1)
                        if len(tao_head) == 2:
                            t_email, t_id = tao_head[0], tao_head[1]
                        else:
                            t_email, t_id = "Unknown", tao_head[0]
                            
                        if user_email and t_email != user_email:
                            continue
                            
                        t_type = parts[1]
                        idx = int(parts[2])
                        
                        if t_id not in tattoos:
                            tattoos[t_id] = {"type": t_type, "email": t_email, "chunks": {}}
                        
                        tattoos[t_id]["chunks"][idx] = parts[4]
                    elif content.startswith("TATTOO:"):
                        if user_email is not None:
                            continue
                            
                        parts = content.split("TATTOO:")[1].split("|")
                        tattoo_id = parts[0]
                        if tattoo_id not in tattoos:
                            tattoos[tattoo_id] = {"type": "old_format"}
                except:
                    continue
    
    if tattoos:
        print("Tattoos currently found on-chain:")
        for t_id, data in tattoos.items():
            t_type = data.get("type")
            t_email = data.get("email", "Unknown")
            
            if t_type == "s":
                chunks = data.get("chunks", {})
                if 1 in chunks:
                    try:
                        b64_payload = chunks[1]
                        decoded_bytes = base64.b64decode(b64_payload)
                        text = decoded_bytes.decode('utf-8', errors='ignore')
                        preview = text[:12]
                        if len(text) > 12:
                            preview += "..."
                        print(f"- [String] Email: {t_email}, ID: {t_id}, Preview: {preview}")
                    except:
                        print(f"- [String] Email: {t_email}, ID: {t_id}, Preview: (Could not decode)")
                else:
                    print(f"- [String] Email: {t_email}, ID: {t_id}, Could not fetch first part of data")
            elif t_type == "f":
                chunks = data.get("chunks", {})
                meta_info = ""
                if 0 in chunks:
                    try:
                        meta_decoded = base64.b64decode(chunks[0]).decode('utf-8')
                        meta_dict = json.loads(meta_decoded)
                        meta_info = f", Original filename: {meta_dict.get('name')}, Size: {meta_dict.get('size')}"
                    except:
                        meta_info = ", Metadata could not be parsed"
                print(f"- [File] Email: {t_email}, ID: {t_id}{meta_info}")
            else:
                print(f"- [Legacy format] ID: {t_id}")
    else:
        print("Could not find any tattoo records matching the criteria.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Solana Digital Tattoo Tool")
    parser.add_argument("action", choices=["upload", "upload_string", "download", "read", "list", "balance"], help="Action to execute")
    parser.add_argument("--file", help="File path (for upload or download destination)")
    parser.add_argument("--string", help="String to tattoo")
    parser.add_argument("--id", help="Unique tattoo ID")
    parser.add_argument("--email", help="User Email")
    args = parser.parse_args()

    if args.action == "upload":
        if not args.file or not args.id or not args.email:
            print("File upload requires --file, --id and --email")
        else:
            check_balances()
            upload(args.file, args.id, args.email)
    elif args.action == "upload_string":
        if not args.string or not args.id or not args.email:
            print("String upload requires --string, --id and --email")
        else:
            check_balances()
            upload_string(args.string, args.id, args.email)
    elif args.action == "download":
        if not args.file or not args.id or not args.email:
            print("Download requires --file, --id and --email")
        else:
            download(args.id, args.file, args.email)
    elif args.action == "read":
        if not args.id or not args.email:
            print("Read requires --id and --email")
        else:
            download(args.id, None, args.email)
    elif args.action == "list":
        if not args.email:
            print("List requires --email")
        else:
            list_tattoos(args.email)
    elif args.action == "balance":
        check_balances()
