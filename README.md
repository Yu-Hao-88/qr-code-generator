# qr-code-generator

## System Requirements

Build a dynamic QR code system where:
- Users submit a long URL and get back a short URL token + QR code image
- The QR code encodes a short URL that redirects (302) to the original URL via your server
- Users can modify the target URL after QR code creation
- Users can delete a QR code (soft delete)
- Users can optionally set an expiration timestamp on create or update
- Deleted or expired links return appropriate HTTP status codes
- URL validation: format check, normalization, malicious URL blocking

## Design Questions

Answer these before you start coding:

**Static vs Dynamic QR Code:** Why does this system use dynamic QR codes (encode short URL) instead of static (encode original URL directly)? When would you choose static instead?

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

選擇 Static 的時機：
- 目標網址很短且永遠不會變。
- 不需要追蹤數據。
- 離線環境（無法依賴 redirect server）。
- 對隱私要求高、不希望流量經過中介伺服器。

**Token Generation:** How will you generate short URL tokens? What happens when two different URLs produce the same token? How does collision probability change as the number of tokens grows?

生成方式：對原始 URL + 時間戳做 SHA256，取前幾 bytes 轉 base62，得到固定長度的 token（例如 8 chars）。

碰撞處理：碰撞理論上永遠可能發生，不能假設不會碰到。系統在寫入前先查 DB，若 token 已被其他 URL 使用，則加鹽重新 hash 後重試，直到取得未使用的 token。

碰撞機率與數量的關係（生日悖論）：
- n 個 token、空間大小 N，碰撞機率 ≈ `1 - e^(-n²/2N)`
- 當 `n ≈ √N` 時，碰撞機率達到約 50%
- 8 chars base62 的空間 N ≈ 218 兆，約 2 億筆 token 才會有 50% 碰撞機率
- 結論：選擇足夠長的 token，讓業務規模內的碰撞機率可忽略不計，再搭配 retry 機制兜底。

**Redirect Strategy:** Why 302 (temporary) instead of 301 (permanent)? What are the trade-offs for analytics, URL modification, and latency?

301（永久重定向）會被瀏覽器快取：下次掃描同一 QR Code，瀏覽器直接跳轉，不經過伺服器。這有兩個問題：
- 無法追蹤掃描次數（請求根本不到伺服器）。
- 若使用者修改了目標網址，舊快取仍會導向舊 URL，直到快取過期。

302（臨時重定向）每次都會過伺服器，因此：
- 可以記錄每次掃描並累積分析數據。
- 目標網址修改後立即生效。
- 代價是多一次網路來回（latency 略高），但對 QR Code 掃描場景影響可忽略。

結論：這個系統需要可修改目標網址 + 追蹤掃描數據，所以必須用 302。

**URL Normalization:** What normalization rules do you need? Why is `http://Example.com/` and `https://example.com` potentially the same URL?

正規化規則：
- scheme 統一轉小寫（`HTTP` → `http`）
- host 統一轉小寫（`Example.com` → `example.com`）
- 移除預設 port（`http://example.com:80` → `http://example.com`）
- 移除結尾多餘的 `/`（`example.com/` → `example.com`）
- 統一 percent-encoding（`%2F` → `/`，未保留字元 decode）
- 移除 fragment（`#section` 不屬於伺服器端識別範圍）

`http://Example.com/` 與 `https://example.com` 正規化後的 host + path 相同，但 scheme 不同（http vs https），嚴格來說仍是不同 URL。系統應以正規化後的完整 URL 作為去重依據，而非部分比對。

**Error Semantics:** What should happen when someone scans a deleted link vs a non-existent link? Should the HTTP status codes be different?

應該使用不同的狀態碼，因為語意不同：
- **404 Not Found**：token 從未存在，伺服器對此資源一無所知。
- **410 Gone**：token 曾經存在，但已被刪除或過期。410 明確告知資源「曾存在且已消失」，語意比 404 更精確。

這個區別對使用者體驗和 SEO 都有意義：搜尋引擎對 410 的處理是移除索引，對 404 則可能持續重試。對於 QR Code 系統，回傳 410 也能讓前端顯示「此連結已失效」而非「找不到頁面」，體驗更好。

## Verification

Your prototype should pass all of these:

```bash
# Create a QR code
curl -X POST http://localhost:8000/api/qr/create \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
# → 200, returns {"token": "...", "short_url": "...", "qr_code_url": "...", "original_url": "..."}

# Redirect
curl -o /dev/null -w "%{http_code}" http://localhost:8000/r/{token}
# → 302

# Get info
curl http://localhost:8000/api/qr/{token}
# → 200, returns token metadata

# Update target URL
curl -X PATCH http://localhost:8000/api/qr/{token} \
  -H "Content-Type: application/json" \
  -d '{"url": "https://new-url.com"}'
# → 200

# Redirect now goes to new URL
curl -o /dev/null -w "%{redirect_url}" http://localhost:8000/r/{token}
# → https://new-url.com

# Delete
curl -X DELETE http://localhost:8000/api/qr/{token}
# → 200

# Redirect after delete
curl -o /dev/null -w "%{http_code}" http://localhost:8000/r/{token}
# → 410

# Non-existent token
curl -o /dev/null -w "%{http_code}" http://localhost:8000/r/INVALID
# → 404

# QR code image
# (create a new one first, then)
curl -o /dev/null -w "%{http_code} %{content_type}" http://localhost:8000/api/qr/{token}/image
# → 200 image/png

# Analytics
curl http://localhost:8000/api/qr/{token}/analytics
# → 200, returns {"token": "...", "total_scans": N, "scans_by_day": [...]}
```