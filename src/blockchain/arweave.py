import os
import time
import mimetypes
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# Arweave Setup
# ============================================================
AR_WALLET = None
AR_RECEIVER_ADDRESS = os.getenv("AR_RECEIVER_ADDRESS", "")
AR_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit for Arweave file tattoos

try:
    from arweave.arweave_lib import Wallet as ArWallet
    from arweave.arweave_lib import Transaction as ArTransaction
    from arweave.transaction_uploader import get_uploader as ar_get_uploader
    from arweave.deep_hash import deep_hash as ar_deep_hash
    from jose.utils import base64url_encode as b64url_enc, base64url_decode as b64url_dec
    ar_key_path = os.getenv("AR_SENDER_KEY", "")
    if ar_key_path and os.path.exists(ar_key_path):
        AR_WALLET = ArWallet(ar_key_path)
        print(f"Arweave wallet loaded: {AR_WALLET.address}")
except ImportError:
    ar_get_uploader = None
    ar_deep_hash = None
    b64url_enc = None
    b64url_dec = None
    pass
except Exception as e:
    ar_get_uploader = None
    ar_deep_hash = None
    b64url_enc = None
    b64url_dec = None
    print(f"Warning: Could not load Arweave wallet: {e}")

# Multiple Arweave gateways for resilience
AR_GRAPHQL_GATEWAYS = [
    "https://arweave-search.goldsky.com/graphql",
    "https://arweave.net/graphql",
]
AR_DATA_GATEWAYS = [
    "https://turbo-gateway.com",
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

# ============================================================
# ArDrive Turbo (ANS-104 Bundled Upload) — free for <100 KiB
# ============================================================
TURBO_UPLOAD_URLS = [
    "https://turbo.ardrive.io/tx/arweave",
    "https://upload.ardrive.io/v1/tx/arweave",
]

def _avro_encode_long(n):
    """Encode integer as Avro long (zigzag + varint)."""
    z = (n << 1) ^ (n >> 63)
    result = bytearray()
    while z > 0x7f:
        result.append((z & 0x7f) | 0x80)
        z >>= 7
        
    result.append(z & 0x7f)
    return bytes(result)

def _serialize_tags_avro(tags_list):
    """Serialize list of (name, value) tuples as ANS-104 Avro-encoded tags."""
    if not tags_list:
        return _avro_encode_long(0)
    items_buf = bytearray()
    for name, value in tags_list:
        nb = name.encode('utf-8') if isinstance(name, str) else name
        vb = value.encode('utf-8') if isinstance(value, str) else value
        items_buf.extend(_avro_encode_long(len(nb)))
        items_buf.extend(nb)
        items_buf.extend(_avro_encode_long(len(vb)))
        items_buf.extend(vb)
    result = bytearray()
    result.extend(_avro_encode_long(len(tags_list)))
    result.extend(items_buf)
    result.extend(_avro_encode_long(0))  # end of array
    return bytes(result)

def ar_build_data_item(data_bytes, tags_dict):
    """Build and sign an ANS-104 DataItem with Arweave RSA-4096 wallet.
    Returns (binary_data_item, data_item_id_string)."""
    import struct
    import hashlib as _hl

    if not AR_WALLET or not ar_deep_hash:
        raise Exception("Arweave wallet or deep_hash not available")

    owner_bytes = b64url_dec(AR_WALLET.owner.encode())
    tags_list = list(tags_dict.items())
    serialized_tags = _serialize_tags_avro(tags_list)

    # DeepHash input for ANS-104 DataItem signing (per arbundles reference)
    sign_data = ar_deep_hash([
        b"dataitem",
        b"1",                       # version
        b"1",                       # signatureType.toString()
        owner_bytes,
        b"",                        # rawTarget (empty when no target)
        b"",                        # rawAnchor (empty when no anchor)
        serialized_tags,            # rawTags (Avro-encoded bytes)
        data_bytes
    ])

    signature = AR_WALLET.sign(sign_data)
    item_id = b64url_enc(_hl.sha256(signature).digest()).decode().rstrip('=')

    buf = bytearray()
    buf.extend(struct.pack('<H', 1))                       # sig type = 1 (Arweave)
    buf.extend(signature)                                   # 512 bytes
    buf.extend(owner_bytes)                                 # 512 bytes
    buf.extend(b'\x00')                                     # no target
    buf.extend(b'\x00')                                     # no anchor
    buf.extend(struct.pack('<Q', len(tags_list)))           # num tags
    buf.extend(struct.pack('<Q', len(serialized_tags)))    # tags byte length
    buf.extend(serialized_tags)
    buf.extend(data_bytes)
    return bytes(buf), item_id

def ar_send_via_turbo(data_bytes, tags_dict):
    """Upload a signed ANS-104 DataItem via ArDrive Turbo. Returns tx_id string."""
    import requests as _req

    data_item, item_id = ar_build_data_item(data_bytes, tags_dict)
    last_error = ""
    for url in TURBO_UPLOAD_URLS:
        try:
            response = _req.post(url, data=data_item,
                                 headers={"Content-Type": "application/octet-stream"}, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return result.get("id", item_id)
            elif response.status_code == 402:
                raise Exception("Turbo: insufficient credits (data exceeds free tier)")
            else:
                last_error = f"HTTP {response.status_code} - {response.text[:100]}"
                print(f"  Turbo {url}: {last_error}")
        except _req.exceptions.ConnectionError:
            last_error = f"{url}: connection error"
            print(f"  Turbo endpoint unreachable, trying next...")
        except Exception as e:
            if "insufficient credits" in str(e):
                raise
            last_error = str(e)
            print(f"  Turbo error: {last_error}")
    raise Exception(f"All Turbo endpoints failed: {last_error}")

def ar_send_tx(data_bytes, tags, description="", max_retries=5):
    """Send a single Arweave transaction with data and tags. Returns tx_id string."""
    import random
    import requests
    
    if not AR_WALLET:
        raise Exception("Arweave wallet not loaded. Check AR_SENDER_KEY in .env")
    
    data_size = len(data_bytes)

    if ar_deep_hash and b64url_enc:
        try:
            tx_id = ar_send_via_turbo(data_bytes, tags)
            print(f"✅ Turbo TX (instant): {tx_id} {description}")
            return tx_id
        except Exception as e:
            print(f"⚠️ Turbo failed, falling back to L1: {e}")

    use_chunked = data_size > 50 * 1024
    
    for attempt in range(max_retries):
        try:
            if use_chunked:
                import tempfile
                
                tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".tattoo_tmp")
                tmp_file.write(data_bytes)
                tmp_file_path = tmp_file.name
                tmp_file.close()
                
                try:
                    fh = open(tmp_file_path, "rb", buffering=0)
                    tx = ArTransaction(AR_WALLET, file_handler=fh, file_path=tmp_file_path)
                    for k, v in tags.items():
                        tx.add_tag(k, v)
                    tx.sign()
                    
                    uploader = ar_get_uploader(tx, fh)
                    
                    print(f"  Chunked upload: {uploader.total_chunks} chunks for {data_size} bytes")
                    while not uploader.is_complete:
                        uploader.upload_chunk()
                        print(f"  Uploaded chunk {uploader.uploaded_chunks}/{uploader.total_chunks} ({uploader.pct_complete}%)")
                    
                    fh.close()
                    tx_id = tx.id
                    print(f"Arweave TX sent and accepted (chunked): {tx_id} {description}")
                    print(f"  ⏳ TX accepted, pending confirmation (~10-20 min for indexing)")
                    return tx_id
                finally:
                    if os.path.exists(tmp_file_path):
                        os.remove(tmp_file_path)
            else:
                tx = ArTransaction(AR_WALLET, data=data_bytes)
                for k, v in tags.items():
                    tx.add_tag(k, v)
                
                tx.sign()
                
                url = f"{tx.api_url}/tx"
                headers = {'Content-Type': 'application/json', 'Accept': 'text/plain'}
                response = requests.post(url, data=tx.json_data, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    tx_id = tx.id
                    print(f"Arweave TX sent and accepted: {tx_id} {description}")
                    
                    try:
                        status_res = requests.get(f"{tx.api_url}/tx/{tx_id}/status", timeout=10)
                        if status_res.status_code == 200:
                            print(f"  ✅ TX confirmed on-chain")
                        elif status_res.status_code == 202 or status_res.text == "Pending":
                            print(f"  ⏳ TX accepted, pending confirmation (~10-20 min for indexing)")
                    except Exception:
                        print(f"  ⏳ TX accepted (status check skipped)")
                    
                    return tx_id
                else:
                    raise Exception(f"Arweave node rejected TX: HTTP {response.status_code} - {response.text[:200]}")
        except (UnboundLocalError, Exception) as e:
            err_msg = str(e)
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


def ar_upload(file_path, tattoo_id, user_email, extra_tags=None):
    """Upload a file to Arweave in a single transaction."""
    file_size = os.path.getsize(file_path)
    if file_size > AR_MAX_FILE_SIZE:
        print(f"Error: File size {file_size} bytes exceeds limit of {AR_MAX_FILE_SIZE} bytes.")
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
        "Content-Type": mimetypes.guess_type(file_name)[0] or "application/octet-stream",
    }
    if extra_tags and isinstance(extra_tags, dict):
        tags.update(extra_tags)
    
    tx_id = ar_send_tx(file_data, tags, f"(file: {file_name})")
    print(f"\nArweave file tattoo completed! Tattoo ID: {tattoo_id}, TX: {tx_id}")
    print(f"⏳ Note: Arweave transactions take ~10-20 minutes to be indexed. List/download may not work immediately.")
    return [tx_id]


def ar_upload_string(text, tattoo_id, user_email, extra_tags=None):
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
    if extra_tags and isinstance(extra_tags, dict):
        tags.update(extra_tags)
    
    tx_id = ar_send_tx(text.encode('utf-8'), tags, f"(string)")
    print(f"\nArweave string tattoo completed! Tattoo ID: {tattoo_id}, TX: {tx_id}")
    print(f"⏳ Note: Arweave transactions take ~10-20 minutes to be indexed. List/download may not work immediately.")
    return [tx_id]


def ar_download(tattoo_id, output_path, user_email):
    """Download tattoo data from Arweave using GraphQL to find the transaction by tags."""
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
    """Download and return data from Arweave given a list of transaction IDs."""
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
