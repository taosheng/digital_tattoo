# Developer Guide: Solana Digital Tattoo (SDT) Project

## Project Overview
The **Solana Digital Tattoo (SDT)** project is a specialized tool designed to achieve data permanence on the Solana blockchain. Unlike standard database storage, this project utilizes the **SPL Memo Program** to shard and "tattoo" arbitrary data (up to 1024KB, such as images or text documents) into the transaction logs of the blockchain. 

Once a transaction is confirmed, the data becomes a permanent part of the Solana ledger—immutable, public, and undeletable.

## Core Concepts
* **Digital Tattoo:** Data is stored in transaction memos rather than in account states. This approach is more cost-effective and prevents the data from being "closed" or "deleted" like traditional storage accounts.
* **Data Sharding:** Since Solana transactions have a Maximum Transmission Unit (MTU) limit of approximately 1,232 bytes, larger payloads are split into ~800-byte chunks, encoded in Base64 format, and indexed sequentially.
* **Indexing Schema:** Every log entry must include the user's email to associate the data with the user. The chunks follow these formats:
   * **For Strings (`s`):** `TAO:<user-email>:<ID>|s|<index>|<total>|<Base64_Payload>`
   * **For Files (`f`):** `TAO:<user-email>:<ID>|f|<index>|<total>|<Base64_Payload>`
     * *Note on File indexing:* For file uploads, index `0` is reserved exclusively for the file's metadata string (e.g., file name, file size), encoded in Base64. The actual file content starts from index `1`.

## User & System Flow
* Users can only sign up and log in via Gmail.
* Upon a user's first sign-up, the system creates a user document in Firestore containing basic user information: user name, Gmail address, Google ID, initial sign-up timestamp, last login timestamp, and user points (default is 5).
* After signing up, users can perform two core functions: (A) tattoo a string, and (B) tattoo a file.
   * **(A) Tattoo a String:** The user can input a string limited to 500 characters. Upon confirmation, the system executes transactions to store the string on the Solana blockchain. Simultaneously, it creates a record in the user's Firestore document containing all necessary retrieval information, including the `TAO` format identifier, type, transaction signatures, sender, receiver, and timestamp.
   * **(B) Tattoo a File:** The user can upload a file of up to 1024KB (default limit configurable via `.env`). If an uploaded image exceeds this limit, the system will automatically compress it to meet the limit. Upon upload, the system shards the file into chunks and executes transactions to securely write each chunk. It then creates a corresponding record in the user's document for retrieval and backs up both the original and compressed files to Vaultsage.ai.
* Each tattoo action consumes one user point. If a user's point balance reaches 0, they cannot perform any new tattoo operations. However, they can still list their existing tattoos and download associated information.
* Users have access to their personal tattoo list and can click on individual entries to view detailed information.

## Hosting Environment
* The project is hosted on Google Cloud Platform (GCP).
* The user's information is stored in GCP Firestore (database name: `tattoo`).
* The system utilizes a service account JSON file to access GCP server-side services (default name: `saltycat.json`).
* Vaultsage.ai is leveraged as a secondary storage solution for user uploads and content. (API usage documentation: https://api.vaultsage.ai/docs)

## Developer Information
* Critical keys, including the Vaultsage personal API key, Solana sender account address, and receiver address, are stored in the local `.env` file.
