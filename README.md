# QR Code Generator

動態 QR Code 生成系統。使用者提交一個長網址，系統回傳短網址 token 與 QR Code 圖片；掃描後由伺服器 302 重新導向至原始 URL。支援修改目標網址、軟刪除、設定過期時間。

---

## System Requirements

- 使用者提交長網址，取得短網址 token + QR Code 圖片
- QR Code 編碼短網址，由伺服器 302 導向原始 URL
- 可在建立後修改目標網址
- 可軟刪除 QR Code
- 可選擇性設定過期時間（建立或更新時）
- 已刪除或已過期的連結回傳對應的 HTTP 狀態碼
- URL 驗證：格式檢查、正規化、惡意網址阻擋

## 技術棧

- **後端**：Python 3.12 / FastAPI / SQLAlchemy / Alembic
- **快取**：Redis（QR Code 圖片快取）
- **資料庫**：SQLite
- **容器**：Docker / Docker Compose
- **前端**：純 HTML + Vanilla JS（無需安裝）

---

## 快速開始

### 前置需求

- Docker & Docker Compose

### 1. 複製設定檔

```bash
cp configs/api.ini.example configs/api.ini
```

依需求修改 `configs/api.ini`：

```ini
[API]
host=0.0.0.0
port=8000
base_url=http://localhost:8000   # 對外的 base URL，影響 QR Code 內嵌的短網址
docs_url=/docs                   # Swagger UI 路徑，留空則關閉
reload=True                      # 開發模式熱重載
workers=1
```

### 2. 啟動服務

```bash
bash run_api_local.sh
```

腳本會依序執行：

1. 重新 build Docker image
2. 執行 Alembic migration（建立資料表）
3. 以 Docker Compose 啟動 `api`（port 8000）與 `redis`（port 6379）

服務啟動後可至 [http://localhost:8000/docs](http://localhost:8000/docs) 查看 Swagger 文件。

---

## 使用前端介面

無需安裝任何工具，直接用瀏覽器開啟：

```
frontend/index.html
```

> 確認左上角的 **API Base URL** 填寫正確（預設 `http://localhost:8000`）。

前端涵蓋所有 API 功能：

| 功能 | 說明 |
|------|------|
| 建立 QR Code | 輸入 URL（可設定過期時間），成功後自動顯示 QR Code 圖片與 token |
| 查詢 QR Code 資訊 | 輸入 token，以表格顯示詳細資訊 |
| 取得 QR Code 圖片 | 輸入 token，顯示圖片並提供下載 |
| 更新 QR Code | 輸入 token 與新 URL，即時生效（掃描舊 QR Code 會導向新網址）|
| 刪除 QR Code | 軟刪除，刪除後掃描回傳 410 Gone |
| 重新導向連結 | 產生掃描用的短網址，點擊可直接測試 302 導向 |

---

## API 說明

所有 API 回傳統一格式：

```json
{
  "status": "success | fail",
  "code": 200,
  "message": "...",
  "data": {}
}
```

### QR Code

#### 建立 QR Code

```
POST /api/qr_code/v1
```

Request body：

```json
{
  "url": "https://example.com",
  "expires_at": "2025-12-31T00:00:00Z"  // 選填
}
```

Response `data`：

```json
{ "qr_token": "abc123" }
```

---

#### 查詢 QR Code 資訊

```
GET /api/qr_code/v1/{qr_token}
```

Rate limit：30 次 / 分鐘

Response `data`：

```json
{
  "token": "abc123",
  "original_url": "https://example.com",
  "created_at": "2025-01-01T00:00:00",
  "updated_at": "2025-01-01T00:00:00",
  "expires_at": null,
  "is_deleted": false
}
```

---

#### 取得 QR Code 圖片

```
GET /api/qr_code/v1/{qr_token}/image
```

Rate limit：30 次 / 分鐘  
回傳 `image/png` 二進位資料。

---

#### 更新 QR Code 目標網址

```
PUT /api/qr_code/v1/{qr_token}
```

Request body：

```json
{ "url": "https://new-url.com" }
```

---

#### 刪除 QR Code

```
DELETE /api/qr_code/v1/{qr_token}
```

軟刪除，資料保留於 DB，掃描後回傳 410 Gone。

---

### 重新導向

```
GET /api/redirect/v1/{qr_token}
```

掃描 QR Code 後觸發，伺服器以 302 導向原始 URL。

| 狀況 | HTTP 狀態碼 |
|------|------------|
| 正常 | 302 Found |
| Token 不存在 | 404 Not Found |
| 已刪除或已過期 | 410 Gone |

---

## 專案結構

```
qr-code-generator/
├── configs/
│   ├── api.ini.example       # API 設定範本
│   └── api.ini               # 本地設定（不進版控）
├── frontend/
│   └── index.html            # 前端介面（直接開啟即可用）
├── libs/
│   ├── controllers/          # 業務邏輯
│   ├── database/             # DB 連線、model、repository
│   ├── models/               # Pydantic request / response schema
│   └── utils/                # 工具（token 生成、rate limiter、例外）
├── routes/
│   ├── main.py               # FastAPI app 進入點
│   ├── qr_code/v1.py         # QR Code 路由
│   └── redirect/v1.py        # 重新導向路由
├── alembic/                  # DB migration
├── Dockerfile
├── run_api_local.sh          # 一鍵啟動腳本
└── run_api_local_docker_compose.yml
```

---

## Design Questions

### Static vs Dynamic QR Code

> Why does this system use dynamic QR codes (encode short URL) instead of static (encode original URL directly)? When would you choose static instead?

Dynamic QR Code 將短網址編進 QR Code，由伺服器負責 redirect 到真正的目標網址。

Static 的問題：
- URL 越長，QR Code 越複雜、密度越高，掃描越困難。
- 一旦生成就不能改，目標網址變更必須重新印刷。
- 無法追蹤掃描數據。

Dynamic 的優點：
- QR Code 只編碼短網址，圖片更簡單、易掃描。
- 可隨時修改目標網址，不需重新印刷 QR Code。
- 可追蹤掃描次數、來源等數據。
- 可設定過期時間、軟刪除等進階控制。

選擇 Static 的時機：目標網址很短且永遠不會變、不需要追蹤數據、離線環境、對隱私要求高。

---

### Token Generation

> How will you generate short URL tokens? What happens when two different URLs produce the same token? How does collision probability change as the number of tokens grows?

生成方式：對原始 URL + 時間戳做 SHA256，取前幾 bytes 轉 base62，得到固定長度的 token（例如 8 chars）。

碰撞處理：系統在寫入前先查 DB，若 token 已被其他 URL 使用，則加鹽重新 hash 後重試，直到取得未使用的 token。

碰撞機率（生日悖論）：8 chars base62 的空間 N ≈ 218 兆，約 2 億筆 token 才會有 50% 碰撞機率。選擇足夠長的 token 讓業務規模內的碰撞機率可忽略不計，再搭配 retry 機制兜底。

---

### Redirect Strategy

> Why 302 (temporary) instead of 301 (permanent)? What are the trade-offs for analytics, URL modification, and latency?

302（臨時重定向）每次都會過伺服器：
- 可以記錄每次掃描並累積分析數據。
- 目標網址修改後立即生效。

301（永久重定向）會被瀏覽器快取：無法追蹤掃描次數、目標網址修改後快取仍導向舊 URL。

---

### URL Normalization

> What normalization rules do you need? Why is `http://Example.com/` and `https://example.com` potentially the same URL?

正規化規則：
- scheme / host 統一轉小寫
- 移除預設 port（`http://example.com:80` → `http://example.com`）
- 移除結尾多餘的 `/`
- 統一 percent-encoding
- 移除 fragment（`#section`）

`http://Example.com/` 與 `https://example.com` 正規化後 host + path 相同，但 scheme 不同，嚴格來說仍是不同 URL。

---

### Error Semantics

> What should happen when someone scans a deleted link vs a non-existent link? Should the HTTP status codes be different?

| 狀況 | 狀態碼 | 說明 |
|------|--------|------|
| Token 從未存在 | 404 Not Found | 伺服器對此資源一無所知 |
| 已刪除或已過期 | 410 Gone | 資源曾存在且已消失 |

410 明確告知資源曾存在，對 SEO 語意更精確；前端也能據此顯示「此連結已失效」而非「找不到頁面」。
