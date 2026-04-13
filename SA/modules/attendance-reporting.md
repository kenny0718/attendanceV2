# attendance-reporting 子文件 SDD

**子域名稱**：`attendance.reporting`  
**你可以把它理解成**：出勤模組裡的「查詢與報表子域」  
**對應主文件**：`SA/modules/attendance.md`  
**主要程式位置**：
- `backend/app/modules/attendance/api/reporting.py`
- `backend/app/modules/attendance/api/reporting_helpers.py`
- `backend/app/modules/attendance/reporting_repo.py`
- `backend/app/modules/attendance/reporting_service.py`
- `backend/app/modules/attendance/reporting_schemas.py`

---

## 1. 這份文件是給誰看的？

如果你要改的是下面這些功能，就先看這份：

- sessions 查詢
- user summary
- company summary
- reporting 的時間區間處理
- Taipei business-date boundary
- reporting response shaping
- 員工個人月視圖
- HR / 管理端的正式列印與異常檢查視圖

白話說：

> 只要是「查資料、做摘要、做報表」而不是「寫打卡事件」，就先看這份。

---

## 2. 這個子域是做什麼的？

`attendance.reporting` 是 attendance 模組裡的唯讀查詢子域。

它的工作是：

- 讀取已經存在的出勤資料
- 依規則查詢與聚合
- 回傳 sessions、user summary、company summary
- 提供員工查閱自己當月紀錄的 read-side 能力
- 提供 HR / 管理端查正式列印內容與異常資訊的 read-side 能力

它**不是** canonical semantic owner。

也就是說：

- 它可以讀 `duration_minutes`
- 但不能自己決定 `duration_minutes` 應該是 gross 還是 net

---

## 3. 主要功能拆解

### 3.1 Sessions List
用途：列出某段時間內的出勤 sessions。

### 3.2 User Summary
用途：計算某個使用者在查詢區間內的摘要。

### 3.3 Company Summary
用途：計算整家公司在查詢區間內的摘要。

### 3.4 Employee Monthly View（P0）
用途：讓員工在手機上查看自己當月的正式出勤紀錄。

設計原則：
- 員工只看自己的資料
- 以正式有效紀錄為主
- 重點是查閱方便、手機易讀
- 不把 HR 內部異常排查資訊直接混進員工視圖

### 3.5 HR Review / Print View（P0）
用途：讓具 HR / 管理身份的人查看正式列印內容、異常資訊與管理檢查資料。

設計原則：
- 正式列印與勞檢備查由 HR / 管理端負責
- 異常、缺卡、補卡、未核准加班等資訊集中在 HR 視圖
- 員工視圖與 HR 視圖應分流

### 3.6 Query Range Validation
用途：驗證 `start_date` / `end_date` 是否為 timezone-aware datetime。

### 3.7 Taipei Business-Date Boundary
用途：把「今天」或日期查詢邊界轉成正確的 Taipei business-date UTC range。

---

## 4. 主要檔案與白話用途

| 檔案 | 白話說明 | 你什麼時候會改到 |
|---|---|---|
| `api/reporting.py` | 報表 API 入口 | 改 sessions / summary endpoint 時 |
| `api/reporting_helpers.py` | 時區與 boundary helper | 改查詢區間規則時 |
| `reporting_repo.py` | reporting read query | 改查詢條件時 |
| `reporting_service.py` | 聚合與摘要計算 | 改 summary 算法時 |
| `reporting_schemas.py` | response schema | 改報表回傳格式時 |

---

## 5. 正式查詢規則

### 5.1 它是唯讀子域
- reporting 只能讀，不應寫 attendance 主資料

### 5.2 它讀的是 canonical persisted duration
- `duration_minutes` 由交易寫入路徑決定
- reporting 不能反過來定義 canonical semantic

### 5.3 查詢區間必須有明確 boundary owner
- `Asia/Taipei` business-date owner 必須單一
- 不可在 breaks 與 reporting 各維護一套 today 規則

### 5.4 時間輸入必須是 aware datetime
- naive datetime 要拒絕，不要偷偷猜時區

### 5.5 員工視角與 HR 視角必須分流
- 員工只需查看自己當月正式紀錄
- 正式列印、勞檢備查、異常檢查由 HR / 管理端處理
- 不要把員工查閱畫面做成 HR 除錯畫面

---

## 6. 查詢流程圖

### 6.1 Sessions

```text
Client
  -> /api/v1/attendance/sessions
  -> Actor / Scope / Feature Gate
  -> validate datetime range
  -> resolve query range to UTC
  -> reporting_repo query
  -> display / response shaping
  -> response
```

### 6.2 User Summary

```text
Client
  -> /api/v1/attendance/reports/user-summary
  -> Actor / Scope / Feature Gate
  -> validate range
  -> reporting_repo query
  -> reporting_service 聚合
  -> response
```

### 6.3 Company Summary

```text
Client
  -> /api/v1/attendance/reports/company-summary
  -> Actor / Scope / Feature Gate
  -> 公司管理層 scope check (`company_admin` / `hr_manager` / `super_admin`)
  -> validate range
  -> reporting_repo query
  -> reporting_service 聚合
  -> response
```

---

## 7. 這個子域的正式邊界

### 它負責
- sessions 查詢
- summary 聚合
- query validation
- boundary helper
- reporting schemas
- 員工月視圖 read model
- HR / 管理端正式列印與異常檢查 read model

### 它不負責
- punch in / punch out 寫入
- close session
- canonical semantic 決策
- break deduction 寫回
- 用報表邏輯偷偷修正原始交易資料

一句話：

> reporting 只負責「解讀與呈現既有資料」，不負責「決定資料應該怎麼被寫」。

---

## 8. 最容易寫錯的地方

1. 在 reporting 內偷偷重新定義 canonical duration
2. 把 boundary logic 寫散到各 endpoint
3. 把 response shaping、權限、查詢、聚合都堆在同一層，讓 API 越來越胖
4. 直接在 reporting 做 transaction-side 補救邏輯
5. 把員工查閱畫面和 HR 異常檢查畫面混在一起

---

## 9. 與 remediation 的對應重點

這個子域最直接對應的風險票包括：

- `P6_F1_BOUNDARY_OWNER_ALIGNMENT`
- `P6_F2_BREAK_PUNCHES_BOUNDARY_REALIGN`（因為會影響 shared boundary contract）
- `P6_F7_REPORTING_BOUNDARY_THINNING`

你可以這樣理解：

- `F1` 是先把 boundary owner 定乾淨
- `F7` 是避免 reporting API 越長越胖

---

## 10. P0 報表設計原則（依目前產品目標補充）

### 10.1 員工端
- 員工只需要在手機上查看自己當月紀錄
- 重點是簡單、清楚、可確認是否有問題
- 不需要看到完整 HR 管理資訊

### 10.2 HR / 管理端
- 正式報表列印、勞檢備查、異常排查由 HR / 管理端處理
- 兼任 HR 的中小企業管理者也應能直接使用
- 應支援正式輸出與管理檢查兩種視角

### 10.3 報表分流原則
- 員工正式查閱 ≠ HR 異常檢查
- 正式報表重視清楚、正式、可查閱
- 管理視圖重視異常、篩選、追蹤與補正

---

## 11. 之後你要改這裡時，先檢查這 5 件事

1. 這是 read-side 問題，還是 write-side 問題？
2. 你有沒有不小心改到 canonical semantic？
3. boundary owner 是不是仍然只有一個？
4. aggregation 是不是還留在 reporting 子域，不要污染交易流？
5. 改完後有沒有同步更新 `attendance.md` 或這份文件？
