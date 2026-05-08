# How to Find Your Digital Tattoos on the Blockchain (Self-Serve Guide)

Your digital tattoos are permanently recorded on the blockchain. Even if our servers shut down, you can always independently retrieve your data using public tools — no application or backend needed.

> **Which blockchain is my tattoo on?**
> - Tattoos created **after May 8, 2026 10:00 AM (UTC+8)** → stored on **Arweave** (see Section A below)
> - Tattoos created **before May 8, 2026 10:00 AM (UTC+8)** → stored on **Solana Devnet** (see Section B below)

---

# Section A — Arweave (Default, after May 8 2026)

Since May 8, 2026, all new tattoos are stored on the **Arweave** permanent storage network. Each tattoo is a single transaction — no chunking required.

## A1. Locate Your Transaction

1. Go to a public Arweave explorer such as [ViewBlock](https://viewblock.io/arweave) or [ArScan](https://arscan.io).
2. Search by your **Transaction ID** (shown in the "想要自己從區塊鏈下載" section of your tattoo record).
3. You will see your transaction with tags like `App-Name: DigitalTattoo`, `Tattoo-ID`, `Tattoo-Email`, `Tattoo-Type`, etc.

Alternatively, query via Arweave GraphQL endpoint (`https://arweave-search.goldsky.com/graphql`):
```graphql
{
  transactions(
    tags: [
      { name: "App-Name", values: ["DigitalTattoo"] },
      { name: "Tattoo-Email", values: ["your-email@gmail.com"] }
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

## A2. Retrieve a String Tattoo

String tattoos on Arweave are stored as **raw UTF-8 text** in the transaction data (not Base64).

**Steps:**
1. Find your Transaction ID from the explorer or GraphQL query.
2. Open `https://arweave.net/<your-transaction-id>` in a browser.
3. The page will display your original text directly!

## A3. Retrieve a File Tattoo

File tattoos on Arweave are stored as **raw binary data** in a single transaction.

**Steps:**
1. Find your Transaction ID.
2. Download the file from `https://arweave.net/<your-transaction-id>`.
3. The original filename is stored in the transaction tag `Tattoo-Filename`. Rename the downloaded file accordingly.

## A4. Understanding Arweave Transaction Tags

Each tattoo transaction includes these searchable tags:

| Tag | Description | Example |
|-----|-------------|---------|
| `App-Name` | Always "DigitalTattoo" | `DigitalTattoo` |
| `Tattoo-Protocol` | Protocol identifier | `TAO` |
| `Tattoo-ID` | Unique tattoo sequence number | `107` |
| `Tattoo-Type` | `s` for string, `f` for file | `s` |
| `Tattoo-Email` | Owner email | `user@gmail.com` |
| `Tattoo-Filename` | Original filename (file tattoos only) | `photo.jpg` |
| `Tattoo-FileSize` | File size in bytes (file tattoos only) | `133640` |
| `Content-Type` | MIME type | `text/plain; charset=utf-8` |

---

# Section B — Solana Devnet (Legacy, before May 8 2026)

Tattoos created before May 8, 2026 are stored on the **Solana Devnet** using the SPL Memo Program.

## B1. Locate the Blockchain Records
1. Use any public block explorer such as [Solana Explorer](https://explorer.solana.com) or [Solscan](https://solscan.io).
2. Enter the official Receiver Wallet Address: `DHTjb119U6MdpHLHVfqn2bddgJWuWi4c3e84WjXzVBZF`.
3. **Important:** Make sure to select **Devnet** cluster in the explorer settings.
4. Navigate to the **Transactions** history tab.
5. Look through the transaction logs for **SPL Memo Program** entries.

## B2. Identify Your Data
Every chunk is tagged with your email. Search for entries starting with:
`TAO:your-email@gmail.com:<Unique_ID>|...`

- `|s|` = **String Tattoo**
- `|f|` = **File Tattoo**

## B3. Reconstructing a String Tattoo (`s`)
Format: `TAO:your-email@gmail.com:<Unique_ID>|s|<index>|<total>|<Base64_Payload>`

**Steps:**
1. Locate your Memo log entry.
2. Copy the `<Base64_Payload>` portion.
3. Paste it into any Base64 decoder (e.g. `base64decode.org`).
4. The decoded result is your original UTF-8 text!

## B4. Reconstructing a File Tattoo (`f`)
Because Solana transactions have strict size limits, files are split into sequential chunks.
Format: `TAO:your-email@gmail.com:<Unique_ID>|f|<index>|<total>|<Base64_Payload>`

**Steps:**
1. **Index 0 (Metadata):** Find the log where `<index>` is `0`. Decode its Base64 payload to get a JSON with the original filename and size (e.g. `{"name": "photo.jpg", "size": 15000}`).
2. **Index 1 to Total:** Find all remaining logs with the same `<Unique_ID>`. Their indices range from `1` to the `<total>` number.
3. **Concatenate:** Copy the Base64 payloads from chunks `1`, `2`, `3`... sequentially into one continuous string (no spaces or line breaks).
4. **Decode:** Pass the joined Base64 string into a Base64-to-file decoder tool.
5. Save the output using the filename from Index 0.
