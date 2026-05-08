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

# ============================================================
# Solana Setup
# ============================================================
RPC_URL = "https://api.devnet.solana.com"
client = Client(RPC_URL)
MEMO_PROGRAM_ID = Pubkey.from_string("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr")

try:
    sender_key = Keypair.from_bytes(bytes(ast.literal_eval(os.getenv("SENDER_SECRET_KEY"))))
    receiver_pub = Pubkey.from_string(os.getenv("RECEIVER_PUBLIC_KEY"))
except Exception as e:
    print(f"Warning: Could not read Solana keys from .env: {e}")
    sender_key = None
    receiver_pub = None

MAX_UPLOAD_SIZE_KB = int(os.getenv("MAX_UPLOAD_SIZE_KB", "1024"))

# ============================================================
# Arweave Setup
# ============================================================
AR_WALLET = None
AR_RECEIVER_ADDRESS = os.getenv("AR_RECEIVER_ADDRESS", "")
AR_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit for Arweave file tattoos

try:
    from arweave.arweave_lib import Wallet as ArWallet
    from arweave.arweave_lib import Transaction as ArTransaction
    ar_key_path = os.getenv("AR_SENDER_KEY", "")
    if ar_key_path and os.path.exists(ar_key_path):
        AR_WALLET = ArWallet(ar_key_path)
        print(f"Arweave wallet loaded: {AR_WALLET.address}")
except ImportError:
    pass
except Exception as e:
    print(f"Warning: Could not load Arweave wallet: {e}")

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

# ============================================================
# Arweave Upload / Download / List Functions
# ============================================================

# Multiple Arweave gateways for resilience
AR_GRAPHQL_GATEWAYS = [
    "https://arweave-search.goldsky.com/graphql",
    "https://arweave.net/graphql",
]
AR_DATA_GATEWAYS = [
    "https://arweave.net",
    "https://arweave.dev",
]

def ar_graphql_query(query):
    """Execute a GraphQL query against Arweave, trying multiple gateways."""
    import httpx
    last_error = None
    for gw in AR_GRAPHQL_GATEWAYS:
        try:
            res = httpx.post(gw, json={"query": query}, timeout=30.0)
            if res.status_code == 200:
                return res.json()
            else:
                last_error = f"{gw} returned {res.status_code}"
                print(f"⚠️ {last_error}, trying next gateway...")
        except Exception as e:
            last_error = f"{gw}: {e}"
            print(f"⚠️ {last_error}, trying next gateway...")
    print(f"❌ All Arweave GraphQL gateways failed. Last error: {last_error}")
    return None

def ar_fetch_data(tx_id):
    """Fetch raw transaction data from Arweave, trying multiple gateways."""
    import httpx
    last_error = None
    for gw in AR_DATA_GATEWAYS:
        try:
            res = httpx.get(f"{gw}/{tx_id}", timeout=60.0, follow_redirects=True)
            if res.status_code == 200:
                return res.content
            else:
                last_error = f"{gw} returned {res.status_code}"
                print(f"⚠️ {last_error}, trying next gateway...")
        except Exception as e:
            last_error = f"{gw}: {e}"
            print(f"⚠️ {last_error}, trying next gateway...")
    return None

def ar_send_tx(data_bytes, tags, description="", max_retries=5):
    """Send a single Arweave transaction with data and tags. Returns tx_id string.
    Includes retry logic to handle rate limits from the Arweave gateway."""
    import random
    
    if not AR_WALLET:
        raise Exception("Arweave wallet not loaded. Check AR_SENDER_KEY in .env")
    
    for attempt in range(max_retries):
        try:
            tx = ArTransaction(AR_WALLET, data=data_bytes)
            for k, v in tags.items():
                tx.add_tag(k, v)
            
            tx.sign()
            
            # Manual send with response checking (library silently ignores errors)
            import requests
            url = f"{tx.api_url}/tx"
            headers = {'Content-Type': 'application/json', 'Accept': 'text/plain'}
            response = requests.post(url, data=tx.json_data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                tx_id = tx.id
                print(f"Arweave TX sent and accepted: {tx_id} {description}")
                
                # Verify TX status
                status_res = requests.get(f"{tx.api_url}/tx/{tx_id}/status", timeout=10)
                if status_res.status_code == 200:
                    print(f"  ✅ TX confirmed on-chain")
                elif status_res.status_code == 202 or status_res.text == "Pending":
                    print(f"  ⏳ TX accepted, pending confirmation (~10-20 min for indexing)")
                
                return tx_id
            else:
                raise Exception(f"Arweave node rejected TX: HTTP {response.status_code} - {response.text[:200]}")
        except (UnboundLocalError, Exception) as e:
            err_msg = str(e)
            # UnboundLocalError = arweave.net/price API failed (rate limit / network)
            if isinstance(e, UnboundLocalError) or "reward" in err_msg.lower():
                print(f"⚠️ Attempt {attempt+1}/{max_retries}: Arweave gateway not responding (rate limit). Retrying...")
            else:
                print(f"⚠️ Attempt {attempt+1}/{max_retries} failed: {err_msg}")
            
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 3 + random.uniform(0, 2)
                print(f"   Waiting {wait_time:.1f}s before retry...")
                time.sleep(wait_time)
            else:
                raise Exception(f"Failed to send Arweave TX after {max_retries} attempts: {err_msg}")


def ar_upload(file_path, tattoo_id, user_email):
    """Upload a file to Arweave in a single transaction (no chunking needed)."""
    if not os.path.exists(file_path):
        print(f"Error: File not found {file_path}")
        return
    
    file_size = os.path.getsize(file_path)
    if file_size > AR_MAX_FILE_SIZE:
        print(f"Error: File size ({file_size / (1024*1024):.2f} MB) exceeds the Arweave limit of {AR_MAX_FILE_SIZE / (1024*1024):.0f} MB.")
        return
    
    with open(file_path, "rb") as f:
        file_data = f.read()
    
    file_name = os.path.basename(file_path)
    print(f"Starting Arweave file tattoo... ID: {tattoo_id}, Email: {user_email}, Size: {file_size} bytes")
    
    tags = {
        "App-Name": "DigitalTattoo",
        "Tattoo-Protocol": "TAO",
        "Tattoo-ID": str(tattoo_id),
        "Tattoo-Type": "f",
        "Tattoo-Email": user_email,
        "Tattoo-Filename": file_name,
        "Tattoo-FileSize": str(file_size),
        "Content-Type": "application/octet-stream",
    }
    
    tx_id = ar_send_tx(file_data, tags, f"(file: {file_name})")
    print(f"\nArweave file tattoo completed! Tattoo ID: {tattoo_id}, TX: {tx_id}")
    print(f"⏳ Note: Arweave transactions take ~10-20 minutes to be indexed. List/download may not work immediately.")
    return [tx_id]


def ar_upload_string(text, tattoo_id, user_email):
    """Upload a string to Arweave in a single transaction."""
    if len(text) > 1000:
        print("Error: String length exceeds limit (1000 characters)")
        return []
    
    print(f"Starting Arweave string tattoo... ID: {tattoo_id}, Email: {user_email}")
    
    tags = {
        "App-Name": "DigitalTattoo",
        "Tattoo-Protocol": "TAO",
        "Tattoo-ID": str(tattoo_id),
        "Tattoo-Type": "s",
        "Tattoo-Email": user_email,
        "Content-Type": "text/plain; charset=utf-8",
    }
    
    tx_id = ar_send_tx(text.encode('utf-8'), tags, f"(string)")
    print(f"\nArweave string tattoo completed! Tattoo ID: {tattoo_id}, TX: {tx_id}")
    print(f"⏳ Note: Arweave transactions take ~10-20 minutes to be indexed. List/download may not work immediately.")
    return [tx_id]


def ar_download(tattoo_id, output_path, user_email):
    """Download tattoo data from Arweave using GraphQL to find the transaction by tags."""
    import httpx
    
    query = """
    query {
        transactions(
            tags: [
                { name: "App-Name", values: ["DigitalTattoo"] },
                { name: "Tattoo-ID", values: ["%s"] },
                { name: "Tattoo-Email", values: ["%s"] }
            ],
            first: 1
        ) {
            edges {
                node {
                    id
                    tags { name value }
                }
            }
        }
    }
    """ % (tattoo_id, user_email)
    
    print(f"Searching Arweave for tattoo ID: {tattoo_id}, Email: {user_email}...")
    result = ar_graphql_query(query)
    
    if not result:
        return None
    
    edges = result.get("data", {}).get("transactions", {}).get("edges", [])
    if not edges:
        print("No Arweave tattoo found for this ID. (Transactions may take ~10-20 min to be indexed)")
        return None
    
    node = edges[0]["node"]
    tx_id = node["id"]
    tags = {t["name"]: t["value"] for t in node["tags"]}
    tattoo_type = tags.get("Tattoo-Type", "f")
    
    print(f"Found Arweave TX: {tx_id}, Type: {tattoo_type}")
    
    # Fetch the raw data
    data = ar_fetch_data(tx_id)
    if not data:
        print(f"Failed to fetch data from Arweave for TX: {tx_id}")
        return None
    
    if tattoo_type == "s":
        text = data.decode('utf-8')
        if output_path:
            with open(output_path, "w") as f:
                f.write(text)
            print(f"String saved to: {output_path}")
        else:
            print(f"\n--- 刺青內容 (Tattoo Content) ---\n{text}\n--------------------------------")
        return text
    else:
        if output_path:
            with open(output_path, "wb") as f:
                f.write(data)
            original_name = tags.get("Tattoo-Filename", "unknown")
            print(f"File saved to: {output_path} (original: {original_name})")
            return True
        else:
            return data


def ar_download_by_tx_ids(tx_ids):
    """Download and return data from Arweave given a list of transaction IDs.
    For Arweave, each tattoo is a single transaction, so we just fetch the first one."""
    if not tx_ids:
        raise Exception("No transaction IDs provided.")
    
    tx_id = tx_ids[0]  # Arweave: single tx per tattoo
    data = ar_fetch_data(tx_id)
    if not data:
        raise Exception(f"Failed to fetch Arweave TX {tx_id} from all gateways")
    
    return data


def ar_list_tattoos(user_email=None):
    """List all tattoos on Arweave for a given email."""
    email_filter = ""
    if user_email:
        email_filter = f', {{ name: "Tattoo-Email", values: ["{user_email}"] }}'
    
    query = """
    query {
        transactions(
            tags: [
                { name: "App-Name", values: ["DigitalTattoo"] }%s
            ],
            first: 100
        ) {
            edges {
                node {
                    id
                    tags { name value }
                }
            }
        }
    }
    """ % email_filter
    
    print(f"Scanning Arweave for tattoo records...")
    if user_email:
        print(f"Filter: Email = {user_email}")
    
    result = ar_graphql_query(query)
    if not result:
        return
    
    edges = result.get("data", {}).get("transactions", {}).get("edges", [])
    if not edges:
        print("No tattoos found on Arweave. (Transactions may take ~10-20 min to be indexed)")
        return
    
    print(f"Tattoos found on Arweave ({len(edges)}):")
    for edge in edges:
        tags = {t["name"]: t["value"] for t in edge["node"]["tags"]}
        tx_id = edge["node"]["id"]
        t_type = tags.get("Tattoo-Type", "?")
        t_id = tags.get("Tattoo-ID", "?")
        t_email = tags.get("Tattoo-Email", "?")
        
        if t_type == "s":
            print(f"- [String] Email: {t_email}, ID: {t_id}, TX: {tx_id}")
        elif t_type == "f":
            fname = tags.get("Tattoo-Filename", "unknown")
            fsize = tags.get("Tattoo-FileSize", "?")
            print(f"- [File] Email: {t_email}, ID: {t_id}, File: {fname}, Size: {fsize}, TX: {tx_id}")


def ar_check_balance():
    """Check Arweave wallet balance."""
    if not AR_WALLET:
        print("Arweave wallet not loaded.")
        return
    print(f"Arweave Wallet Address: {AR_WALLET.address}")
    try:
        balance = AR_WALLET.balance
        print(f"Arweave Balance: {balance} winston ({float(balance) / 1e12:.6f} AR)")
    except Exception as e:
        print(f"Could not fetch Arweave balance: {e}")


# ============================================================
# CLI Entry Point
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Digital Tattoo Tool (Solana / Arweave)")
    parser.add_argument("action", choices=["upload", "upload_string", "download", "read", "list", "balance"], help="Action to execute")
    parser.add_argument("--file", help="File path (for upload or download destination)")
    parser.add_argument("--string", help="String to tattoo")
    parser.add_argument("--id", help="Unique tattoo ID")
    parser.add_argument("--email", help="User Email")
    parser.add_argument("--blockchain", choices=["solana", "arweave"], default="solana", help="Blockchain to use (default: solana)")
    args = parser.parse_args()

    use_arweave = (args.blockchain == "arweave")

    if args.action == "upload":
        if not args.file or not args.id or not args.email:
            print("File upload requires --file, --id and --email")
        elif use_arweave:
            ar_check_balance()
            ar_upload(args.file, args.id, args.email)
        else:
            check_balances()
            upload(args.file, args.id, args.email)
    elif args.action == "upload_string":
        if not args.string or not args.id or not args.email:
            print("String upload requires --string, --id and --email")
        elif use_arweave:
            ar_check_balance()
            ar_upload_string(args.string, args.id, args.email)
        else:
            check_balances()
            upload_string(args.string, args.id, args.email)
    elif args.action == "download":
        if not args.file or not args.id or not args.email:
            print("Download requires --file, --id and --email")
        elif use_arweave:
            ar_download(args.id, args.file, args.email)
        else:
            download(args.id, args.file, args.email)
    elif args.action == "read":
        if not args.id or not args.email:
            print("Read requires --id and --email")
        elif use_arweave:
            ar_download(args.id, None, args.email)
        else:
            download(args.id, None, args.email)
    elif args.action == "list":
        if not args.email:
            print("List requires --email")
        elif use_arweave:
            ar_list_tattoos(args.email)
        else:
            list_tattoos(args.email)
    elif args.action == "balance":
        if use_arweave:
            ar_check_balance()
        else:
            check_balances()
