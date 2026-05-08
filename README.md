# Digital Tattoo 數位刺青

**Permanently immortalize your data on the blockchain — it will never disappear.**

Digital Tattoo is a web application that lets you "tattoo" text or images onto the blockchain. Once written, your data is permanently stored and publicly verifiable — no server, no company, no single point of failure can ever erase it.

## What It Does

- **String Tattoo (文字刺青):** Write up to 1,000 characters of text permanently onto the blockchain. Ideal for personal messages, quotes, commitments, or any text you want to last forever.
- **Image Tattoo (圖像刺青):** Upload an image (up to 10MB) directly onto the blockchain. The original file is stored as-is in a single transaction, and a compressed WebP preview is generated for fast retrieval.
- **Self-Serve Retrieval:** Every tattoo can be independently retrieved by anyone using public blockchain explorers — no need for our application or servers. Your data is truly yours.
- **Backup:** Original files and WebP previews are additionally backed up to [VaultSage](https://vaultsage.ai) for instant access, while the blockchain copy serves as the ultimate permanent source of truth.

## Architecture

```
┌──────────────┐     ┌──────────────────┐     ┌────────────────┐
│   Frontend   │────▶│  FastAPI Backend  │────▶│    Arweave     │
│  (Vite + JS) │     │  (Cloud Run)     │     │  (Blockchain)  │
└──────────────┘     └──────────────────┘     └────────────────┘
                            │                         │
                            ▼                         │
                     ┌──────────────┐                 │
                     │  Firestore   │  Tattoo records │
                     │  (Database)  │  & user data    │
                     └──────────────┘                 │
                            │                         │
                            ▼                         │
                     ┌──────────────┐                 │
                     │  VaultSage   │  File backup    │
                     │  (Storage)   │  (fast access)  │
                     └──────────────┘                 │
```

- **Frontend:** Vanilla JS + Vite, deployed as static files served by the backend.
- **Backend:** Python FastAPI running on Google Cloud Run.
- **Database:** Google Firestore — stores user accounts, points, and tattoo metadata (TX IDs, filenames, etc.).
- **Blockchain:** Arweave — permanent, decentralized storage for the actual tattoo data.
- **File Backup:** VaultSage — fast-access backup of original and WebP files.

## Why Arweave?

We originally built Digital Tattoo on **Solana** (devnet). It worked, but we discovered a fundamental irony:

> **Solana itself uses Arweave for permanent data storage.**
>
> Solana's block history is not permanently retained by validators. Old ledger data is archived to external storage — and one of the primary archival targets is Arweave. In other words, Solana depends on Arweave for its own long-term data permanence.

This insight led us to cut out the middleman. Instead of writing data to Solana (which would eventually archive it to Arweave anyway), we write directly to Arweave:

| | Solana (before) | Arweave (now) |
|---|---|---|
| **Data permanence** | Depends on validators + archival | Native — data stored forever by design |
| **Transactions per file** | Hundreds (due to ~1KB memo limit) | **One** (up to 10MB per TX) |
| **Upload time** | ~2 hours for a small image | **~30 seconds** |
| **Cost model** | Per-transaction fees (adds up fast) | One-time storage fee (pay once, store forever) |
| **Network** | Devnet (test network) | **Mainnet (production)** |
| **String limit** | 500 characters | **1,000 characters** |

### Backward Compatibility

Tattoos created before May 8, 2026 remain on Solana devnet and are fully retrievable. The system automatically detects which blockchain each tattoo is on via the `blockchain` field in the database record.

## How to Find Your Tattoo

You never depend on us. Every tattoo can be independently verified and retrieved:

- **English guide:** [find_your_tattoo.md](find_your_tattoo.md)
- **繁體中文指南:** [find_your_tattoo_zh_TW.md](find_your_tattoo_zh_TW.md)

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | Vanilla JavaScript, Vite |
| Backend | Python, FastAPI, Uvicorn |
| Auth | Google OAuth 2.0 |
| Database | Google Firestore |
| Blockchain | Arweave (mainnet) |
| Legacy Blockchain | Solana (devnet) |
| File Backup | VaultSage API |
| Deployment | Docker, Google Cloud Run |
| CLI Tool | `src/tattoo.py` (supports both Arweave and Solana) |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
cd src/frontend && npm install && npm run dev   # Frontend (dev server)
cd src/backend && uvicorn main:app --reload     # Backend (API)

# Deploy to Cloud Run
./deploy.sh
```

## Project Structure

```
digital_tattoo/
├── src/
│   ├── tattoo.py              # Core blockchain logic (Arweave + Solana)
│   ├── backend/
│   │   ├── main.py            # FastAPI server
│   │   └── requirements.txt   # Python dependencies
│   └── frontend/
│       └── src/main.js        # Web UI
├── developer.md               # Technical documentation
├── find_your_tattoo.md        # Self-serve retrieval guide (EN)
├── find_your_tattoo_zh_TW.md  # Self-serve retrieval guide (繁中)
├── Dockerfile                 # Multi-stage build
├── deploy.sh                  # Cloud Run deployment
└── .env                       # Configuration (keys, API tokens)
```

## License

This project is for educational and personal use.
