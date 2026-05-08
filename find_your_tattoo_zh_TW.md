# 如何在區塊鏈上找回您的數位刺青 (自助指南)

您的數位刺青已被永久記錄在區塊鏈上。即使我們的伺服器關閉，您也可以隨時隨地利用公開工具獨立找回您的資料，完全不需要依賴我們的應用程式或後端系統。

> **我的刺青在哪條區塊鏈上？**
> - **2026 年 5 月 8 日上午 10:00 (UTC+8) 之後**建立的刺青 → 存放在 **Arweave** 永久儲存網路上（請參考 **A 章節**）
> - **2026 年 5 月 8 日上午 10:00 (UTC+8) 之前**建立的刺青 → 存放在 **Solana Devnet** 上（請參考 **B 章節**）

---

# A 章節 — Arweave（預設，2026/5/8 之後）

自 2026 年 5 月 8 日起，所有新建刺青均存放於 **Arweave** 永久儲存網路上。每一個刺青就是一筆獨立的交易 — 不需要分片。

## A1. 找到您的交易紀錄

1. 前往公開的 Arweave 區塊鏈瀏覽器，例如 [ViewBlock](https://viewblock.io/arweave) 或 [ArScan](https://arscan.io)。
2. 使用您的 **交易 ID (Transaction ID)** 進行搜尋（交易 ID 可在您的刺青紀錄中「想要自己從區塊鏈下載」區域找到）。
3. 您將看到交易中的標籤 (Tags)，包含 `App-Name: DigitalTattoo`、`Tattoo-ID`、`Tattoo-Email`、`Tattoo-Type` 等。

您也可以透過 Arweave GraphQL 端點 (`https://arweave-search.goldsky.com/graphql`) 查詢：
```graphql
{
  transactions(
    tags: [
      { name: "App-Name", values: ["DigitalTattoo"] },
      { name: "Tattoo-Email", values: ["您的信箱@gmail.com"] }
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

## A2. 取回字串刺青

Arweave 上的字串刺青是以 **原始 UTF-8 純文字**直接儲存在交易資料中（非 Base64 編碼）。

**步驟：**
1. 從瀏覽器或 GraphQL 查詢中找到您的交易 ID。
2. 在瀏覽器中開啟 `https://arweave.net/<您的交易ID>`。
3. 頁面會直接顯示您當初紀錄的原始文字！

## A3. 取回檔案刺青

Arweave 上的檔案刺青是以 **原始二進位檔案**儲存在單筆交易中。

**步驟：**
1. 找到您的交易 ID。
2. 從 `https://arweave.net/<您的交易ID>` 下載檔案。
3. 原始檔案名稱存放在交易標籤 `Tattoo-Filename` 中，請依此名稱重新命名下載的檔案即可。

## A4. Arweave 交易標籤說明

每筆刺青交易都包含以下可搜尋的標籤：

| 標籤 | 說明 | 範例 |
|------|------|------|
| `App-Name` | 固定為 "DigitalTattoo" | `DigitalTattoo` |
| `Tattoo-Protocol` | 協議識別碼 | `TAO` |
| `Tattoo-ID` | 刺青唯一編號 | `107` |
| `Tattoo-Type` | `s` 字串, `f` 檔案 | `s` |
| `Tattoo-Email` | 擁有者電子郵件 | `user@gmail.com` |
| `Tattoo-Filename` | 原始檔案名稱（僅限檔案刺青） | `photo.jpg` |
| `Tattoo-FileSize` | 檔案大小 (bytes)（僅限檔案刺青） | `133640` |
| `Content-Type` | MIME 類型 | `text/plain; charset=utf-8` |

---

# B 章節 — Solana Devnet（舊版，2026/5/8 之前）

2026 年 5 月 8 日之前建立的刺青存放在 **Solana Devnet** 上，使用的是 SPL Memo Program。

## B1. 尋找區塊鏈紀錄
1. 開啟任何公開的區塊鏈瀏覽器，例如 [Solana Explorer](https://explorer.solana.com) 或 [Solscan](https://solscan.io)。
2. 輸入官方接收者錢包地址：`DHTjb119U6MdpHLHVfqn2bddgJWuWi4c3e84WjXzVBZF`。
3. **重要：** 請確認瀏覽器已切換到 **Devnet** 叢集。
4. 導航至 **Transactions (交易紀錄)** 分頁。
5. 檢查交易日誌，特別尋找標註有 **SPL Memo Program** 的指令內容。

## B2. 辨識您的資料
每一個資料分片 (Chunk) 都明確標記了您的電子郵件信箱。
搜尋以下格式開頭的紀錄：
`TAO:您的信箱@gmail.com:<唯一_ID>|...`

- `|s|` = **字串 (String) 刺青**
- `|f|` = **檔案 (File) 刺青**

## B3. 重建您的字串刺青 (`s`)
格式：`TAO:您的信箱@gmail.com:<唯一_ID>|s|<序號>|<總數>|<Base64_內容資料>`

**步驟：**
1. 找到您對應的 Memo 日誌紀錄。
2. 複製文字的最後一段，也就是 `<Base64_內容資料>` 的部分。
3. 將這段字串貼到網路上任何標準的 Base64 解碼工具（例如 `base64decode.org`）。
4. 解碼後的結果，即為您最初紀錄的純文字 UTF-8 訊息！

## B4. 重建您的檔案刺青 (`f`)
由於 Solana 的基礎單筆交易資料量有著嚴格的限制，較大的檔案會被「切割 (Sharding)」成好幾個連續的分片。
格式：`TAO:您的信箱@gmail.com:<唯一_ID>|f|<序號>|<總數>|<Base64_內容資料>`

**步驟：**
1. **分片序號 0 (Metadata)：** 尋找 `<序號>` 為 `0` 的日誌。解碼 Base64 內容會得到一個 JSON 結構，記載原始檔名與大小（例如：`{"name": "photo.jpg", "size": 15000}`）。
2. **分片序號 1 至 總數：** 尋找所有擁有相同 `<唯一_ID>` 的日誌。序號從 `1` 排列到 `<總數>` 所標示的數字。
3. **字串拼接：** 將序號 `1`, `2`, `3` ... 的 Base64 內容資料依序複製並拼接成一整串（請務必確保中間沒有留下任何空白或換行）。
4. **還原解碼：** 將拼接完成的 Base64 字串送入 Base64-to-File 解碼工具中。
5. 使用在「分片序號 0」查到的原始檔名儲存輸出結果，即大功告成！
