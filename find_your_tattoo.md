# How to Find Your Digital Tattoos on Solana (Self-Serve Guide)

Since your digital tattoos are permanently etched into the Solana blockchain, you never have to worry about our servers shutting down! You can independently retrieve and reconstruct your data anytime, from anywhere, without using our application or backend.

## 1. Locate the Blockchain Records
All digital tattoos are stored securely inside transaction "memos" under a designated vault wallet address on the Solana network. 
1. Use any public block explorer such as [Solana Explorer](https://explorer.solana.com) or [Solscan](https://solscan.io).
2. Enter the official centralized Receiver Wallet Address: `DHTjb119U6MdpHLHVfqn2bddgJWuWi4c3e84WjXzVBZF`.
3. Navigate to the **Transactions** history tab.
4. Look through the transaction logs and inspect the "Program Instructions" specifically for **SPL Memo Program** entries.

## 2. Identify Your Data
Every single chunk of data you've uploaded is explicitly tagged with your email.
Open the Memo logs and search for your email. You will find entries starting with:
`TAO:your-email@gmail.com:<Unique_ID>|...`

The characters exactly following the `|` pipe define what kind of tattoo it is:
- `|s|` represents a **String Tattoo**
- `|f|` represents a **File Tattoo**

---

## 3. Reconstructing a String Tattoo (`s`)
String tattoos normally take up exactly 1 transaction chunk. The format looks natively like this:
`TAO:your-email@gmail.com:<Unique_ID>|s|<index>|<total>|<Base64_Payload>`

**Steps:**
1. Locate your Log Memo.
2. Copy the final section of the text, which is the `<Base64_Payload>`.
3. Paste that copied string into any online standard Base64 string decoder (like `base64decode.org`). 
4. The decoded result is your original plain-text UTF-8 string!

---

## 4. Reconstructing a File Tattoo (`f`)
Because Solana transactions have a strict size limit, larger files are "sharded" (split) into multiple sequenced chunks. The format is similar:
`TAO:your-email@gmail.com:<Unique_ID>|f|<index>|<total>|<Base64_Payload>`

**Steps:**
1. **Index 0 (Metadata):** Find the log where `<index>` is exactly `0`. The Payload here does **not** contain your file. Instead, decoding this Base64 payload will yield a JSON text structure detailing your original file's native Name and Size (e.g. `{"name": "photo.jpg", "size": 15000}`).
2. **Index 1 to Total (File Data):** Find all remaining logs sharing the exact same `<Unique_ID>`. Their indices will range from `1` entirely up to the number listed in `<total>`.
3. **Concatenate:** Copy the Base64 payloads from chunks `1`, `2`, `3` ... sequentially. Paste them together into one massive, continuous string block (make absolutely sure there are no spaces or breaks in between).
4. **Decode:** Pass this massive joined Base64 block into a Base64-to-File decoder tool or script. 
5. Save the output binary stream using the exact original filename and extension you discovered back in Index 0!
