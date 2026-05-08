# Developer Guide: Digital Tattoo Project

## Project Overview
The **Digital Tattoo** project is a specialized tool designed to achieve data permanence on the blockchain. It allows users to "tattoo" arbitrary data (text up to 1,000 characters, or images up to 10MB) permanently onto the blockchain. Once a transaction is confirmed, the data becomes immutable, public, and undeletable.

**Current blockchain: Arweave (mainnet)** — all new tattoos since May 8, 2026 use Arweave.
Legacy tattoos (before May 8, 2026) remain on Solana devnet and are fully retrievable.

---

## Blockchain Architecture

### Arweave (Primary — since May 8, 2026)

Arweave is a permanent storage network where data is stored in single transactions with no chunking required at the application level.

#### How Data Is Stored

- **String tattoos:** Raw UTF-8 text is stored directly as the transaction data payload.
- **File tattoos:** Raw binary file data is stored as the transaction data payload (original file, not compressed).
- **Metadata:** Stored in transaction **tags** (key-value pairs indexed by Arweave gateways).

#### Transaction Tags

Every Arweave tattoo transaction includes these tags:

| Tag | Description | Example |
|-----|-------------|---------|
| `App-Name` | Always `DigitalTattoo` | `DigitalTattoo` |
| `Tattoo-Protocol` | Protocol identifier | `TAO` |
| `Tattoo-ID` | Unique tattoo sequence number | `107` |
| `Tattoo-Type` | `s` for string, `f` for file | `s` |
| `Tattoo-Email` | Owner email | `user@gmail.com` |
| `Content-Type` | MIME type of the data | `text/plain; charset=utf-8` |
| `Tattoo-Filename` | Original filename (file only) | `photo.jpg` |
| `Tattoo-FileSize` | File size in bytes (file only) | `133640` |

#### Upload Mechanism

The `ar_send_tx()` function in `tattoo.py` handles all Arweave uploads:

- **Data ≤ 50KB:** Single inline POST to `/tx` endpoint (JSON body with base64-encoded data).
- **Data > 50KB:** Chunked upload via the `TransactionUploader`:
  1. Transaction metadata (tags + signature) is POSTed to `/tx` without data.
  2. File data is uploaded in 256KB chunks via `/chunk` endpoint.
  3. Progress is reported per chunk.

This split is necessary because `arweave.net`'s nginx proxy rejects POST bodies larger than ~2MB (HTTP 413), and base64 encoding inflates size by ~33%.

#### Gateway Configuration

Arweave gateways can be unreliable. The system uses multi-gateway fallback:

- **GraphQL queries** (listing tattoos): `arweave-search.goldsky.com` → `arweave.net`
- **Data fetching** (downloading tattoos): `arweave.net` → `arweave.dev`
- **Transaction submission:** `arweave.net` (via wallet's `api_url`)

#### Querying Tattoos (GraphQL)

```graphql
{
  transactions(
    tags: [
      { name: "App-Name", values: ["DigitalTattoo"] },
      { name: "Tattoo-Email", values: ["user@gmail.com"] }
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
```

#### Key Functions (`tattoo.py`)

| Function | Purpose |
|----------|---------|
| `ar_send_tx(data, tags)` | Send transaction (auto-selects inline vs chunked) |
| `ar_upload(file_path, id, email)` | Upload file tattoo |
| `ar_upload_string(text, id, email)` | Upload string tattoo |
| `ar_download_by_tx_ids(tx_ids)` | Download data by transaction IDs |
| `ar_list_tattoos(email, id)` | List tattoos via GraphQL |
| `ar_graphql_query(query)` | Execute GraphQL with gateway fallback |
| `ar_fetch_data(tx_id)` | Fetch raw data with gateway fallback |

#### Retry & Error Handling

- `ar_send_tx`: 5 retries with exponential backoff (3s, 6s, 9s, 12s, 15s + jitter)
- Handles `UnboundLocalError` from arweave-python-client library bug (gateway rate limits cause `get_reward()` to fail)
- Handles HTTP 413 by routing to chunked upload
- `TransactionUploader` import is at **module level** to avoid `signal only works in main thread` error in background threads

#### Indexing Latency

Arweave transactions take **~10–20 minutes** to be indexed by GraphQL gateways after broadcast. During this window:
- `list` command will not find the tattoo
- `read` for string tattoos returns `{"pending": true}` to the frontend
- The frontend shows "交易尚未完成，請稍候幾分鐘後再試"

---

### Solana Devnet (Legacy — before May 8, 2026)

Legacy tattoos use the SPL Memo Program on Solana devnet. Data is sharded into ~800-byte Base64 chunks.

#### Memo Format

- **String:** `TAO:<email>:<ID>|s|<index>|<total>|<Base64_Payload>`
- **File:** `TAO:<email>:<ID>|f|<index>|<total>|<Base64_Payload>`
  - Index `0` = metadata JSON (`{"name":"photo.webp","size":61440}`)
  - Index `1` to `<total>` = file content chunks

#### Encoding Pipeline

- **String:** `original text` → `UTF-8 bytes` → `Base64 string` → memo
- **File:** `binary file` → `Base64 string` → split into 800-char chunks → memos

#### Solana Configuration

| Key | Value |
|-----|-------|
| Receiver Address | `DHTjb119U6MdpHLHVfqn2bddgJWuWi4c3e84WjXzVBZF` |
| Network | Devnet (`https://api.devnet.solana.com`) |
| TX size limit | ~1,232 bytes per transaction |

---

## Limits

| Parameter | Arweave (current) | Solana (legacy) |
|-----------|--------------------|-----------------|
| String length | 1,000 characters | 500 characters |
| File upload size | 10 MB | 2 MB |
| WebP target size | 150 KB | 64 KB |
| Transactions per file | 1 | Hundreds |
| Tattoo data stored | Original file | Compressed WebP |

---

## Database Schema (Firestore)

Database name: `tattoo`

### User Document (`users/{email}`)

| Field | Type | Description |
|-------|------|-------------|
| `email` | string | User email |
| `name` | string | Display name |
| `google_id` | string | Google OAuth sub |
| `points` | number | Remaining tattoo credits (default: 5) |
| `latest_ID` | number | Last used tattoo sequence number |
| `first_signup` | string | ISO timestamp |
| `last_login` | string | ISO timestamp |

### Tattoo Document (`users/{email}/tattoos/{tattoo_id}`)

| Field | Type | Description |
|-------|------|-------------|
| `tattoo_id` | string | Unique sequence ID |
| `type` | string | `"string"` or `"file"` |
| `blockchain` | string | `"arweave"` or absent (= solana) |
| `preview` | string | First 20 chars (string tattoos) |
| `signatures` | array | TX IDs (Arweave) or signatures (Solana) |
| `timestamp` | string | ISO timestamp |
| `uploading_status` | string | File upload progress (file tattoos only) |
| `filename` | string | Stored filename |
| `original_filename` | string | User's original filename |
| `original_size` | number | Original file size in bytes |
| `webp_filename` | string | Generated WebP filename |
| `webp_size` | number | WebP file size in bytes |
| `vaultsage_path` | string | VaultSage directory path |
| `vaultsage_files` | array | List of backed-up filenames |

**Backward compatibility:** If `blockchain` field is missing, the system defaults to `"solana"` for retrieval.

---

## User & System Flow

1. Users sign up and log in via **Google OAuth 2.0**.
2. First signup creates a Firestore user document with 5 default points.
3. Users can:
   - **(A) Tattoo a String:** Up to 1,000 characters. Stored as a single Arweave transaction.
   - **(B) Tattoo an Image:** Up to 10MB. Original file stored on Arweave. WebP preview (≤150KB) generated for fast access. Both original and WebP backed up to VaultSage.
4. Each tattoo consumes **1 point**. At 0 points, users can still view/download existing tattoos.
5. File uploads run in a **background task** (FastAPI `BackgroundTasks`) with status tracking via `uploading_status` field.

---

## Environment Variables (`.env`)

| Variable | Description |
|----------|-------------|
| `SENDER_SECRET_KEY` | Solana sender wallet secret key (legacy) |
| `RECEIVER_PUBLIC_KEY` | Solana receiver wallet address (legacy) |
| `AR_SENDER_KEY` | Path to Arweave JWK wallet file |
| `AR_SENDER_ADDRESS` | Arweave wallet public address |
| `VITE_GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to GCP service account JSON |
| `VAULTSAGE_API_KEY` | VaultSage API key for file backup |

---

## Hosting & Deployment

- **Platform:** Google Cloud Run (Docker container)
- **Database:** GCP Firestore (database name: `tattoo`)
- **Service Account:** `saltycat.json`
- **Memory:** 2 GiB (for processing up to 10MB image uploads)
- **Deploy:** `./deploy.sh` (builds Docker image, pushes to GCR, deploys to Cloud Run)

### Docker Build

Multi-stage build:
1. **Stage 1 (Node):** Builds Vite frontend → `dist/`
2. **Stage 2 (Python):** Installs backend deps, copies source + config files + Arweave wallet, serves via Uvicorn

### CLI Tool

`src/tattoo.py` supports both blockchains via `--blockchain` flag:

```bash
# Arweave (default for new tattoos)
python src/tattoo.py --blockchain arweave --string "永遠的文字" --email user@gmail.com --id 1 upload_string
python src/tattoo.py --blockchain arweave --file photo.jpg --email user@gmail.com --id 2 upload
python src/tattoo.py --blockchain arweave --email user@gmail.com list
python src/tattoo.py --blockchain arweave --email user@gmail.com --id 1 read

# Solana (legacy)
python src/tattoo.py --string "text" --email user@gmail.com --id 1 upload_string
python src/tattoo.py --email user@gmail.com list
```

---

## Dependencies

### Backend (`src/backend/requirements.txt`)

| Package | Purpose |
|---------|---------|
| `fastapi` | Web framework |
| `uvicorn` | ASGI server |
| `firebase-admin` | Firestore access |
| `arweave-python-client` | Arweave blockchain interaction |
| `solana` / `solders` | Solana blockchain (legacy) |
| `Pillow` | Image processing (WebP conversion) |
| `httpx` | HTTP client (VaultSage API) |
| `python-dotenv` | Environment variable loading |

### Known Library Issues (`arweave-python-client`)

1. **`get_reward()` UnboundLocalError:** When `arweave.net/price` returns non-200, the `reward` variable is never assigned. Mitigated by retry logic in `ar_send_tx`.
2. **`tx.send()` silent failure:** The library doesn't check HTTP response status. We manually POST and verify the response.
3. **`signal()` in threads:** `transaction_uploader.py` calls `signal(SIGPIPE, SIG_DFL)` at import time, which fails in non-main threads. Fixed by importing at module level.
