
# Developer Guide: Solana Digital Tattoo (SDT) Project

## Project Overview
The **Solana Digital Tattoo (SDT)** project is a specialized tool designed to achieve data permanence on the Solana blockchain. Unlike standard database storage, this project utilizes the **SPL Memo Program** to shard and "tattoo" arbitrary data (up to 50KB, such as images or text files) into the transaction logs of the blockchain. 

Once a transaction is confirmed, the data becomes a permanent part of the Solana ledger—immutable, public, and undeletable.

## Core Concepts
* **Digital Tattoo:** Data stored in transaction memos rather than account state. It is cheaper and cannot be "closed" or "deleted" like a storage account.
* **Data Sharding:** Since Solana transactions have a MTU limit (approx. 1,232 bytes), files are split into ~800-byte chunks, encoded in Base64, and indexed.
* **Indexing Schema:** Each chunk follows the format: `TAO:<ID>|<type>|<Index>|<Total>|<Base64_Payload>`.
  ** there are only 2 types: "s" or "f", "s" means the tattoo is a UTF-8 string, "f" means tattoo is  file encoded in Base64 format.

## User/System flow
* User can sign-up/login via gmail only
* If it is user's first sign-up, system will create a user document in Firestore which has user basic information: user name, user gmail, user google-id, user first signup timestamp, user last login timestamp, user points (default is 5)
* after sign up, user can do two function (A) tattoo a string (B) tattoo a file
** (A) tattoo a string: user can input a string, limited size to 500 char: once confirm tattoo a string, system will do transaction (one should be enough) to store the string to SOL, at the mean time, it will store a record in users document for all necessary informaiton to get the string from SOL, including TAO:<ID>, type and the transaction information, sender, receiver ,the tattoo timestamp..etc.
** (B) tattoo a file: user can use a button to upload a file. limitd size to 50K, if the file is bigger than 50K and it is an image, then system will automaticailly reduce the size to lower than 50K. Once file uploaded,  system will do transaction (one should be enough) to separate file to chunks so for each chunck can be store in one transactions. After that it will store a record in user's document for all necessary information needed to get the file from SOL, including tattoo timestamp, transaction information , sender ,receiver..etc. System will also backup the original size file and reduced size file to vaultsage.ai

** Every tattoo action user do will reduce one user point. If user point is 0, then user can't do tattoo. However, user still can list existing tattoo and download information
** User will see his tattoo list. and can click the list to see the information

## Hosting env
* This project will be hosted in GCP
* User can only sign-up, login via gmail
* User's information store in GCP Firestore and this project will use a json file to access GCP server side.
 - Firestore database name:tattoo
 - load json file default name: saltycat.json
* This project will leverage vaultsage as storage, to store user's upload file or content. API usage See-> https://api.vaultsage.ai/docs

## Developer infromation
** .env file contains critical keys. including vaultsage personal API key, SOL account sender address, receiver address

