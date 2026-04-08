# 系統架構圖與功能驗證基線

> 目的：把目前系統的正式架構，以**可直接拿來驗證功能歸屬**的圖像化方式整理出來。  
> 使用方式：當你要判斷某功能應該保留、修正、搬移、獨立成模組，先看這份，再對照 `SA/architecture/PLANNED_VS_IMPLEMENTED_MATRIX.md`。

---

## 1. 這份文件要解決什麼問題

你先前的原始藍圖是在偏 `vibe coding` 的情境下逐步形成，過程中很容易被實作或 AI 的臨時建議牽著走，因此會出現：

- 原始規劃與現況實作不完全一致
- 功能先做了，但模組歸屬不夠穩定
- 某些能力原本想做獨立模組，後來先塞進既有模組
- 回頭看時，難以判斷「這是設計選擇」還是「臨時妥協」

這份文件的用途就是提供一個**現況可驗證的系統架構圖基線**，讓你之後補完整 SDD 時，有一張可以反覆對照的圖。

---

## 2. 使用規則

當你在判斷某功能該往哪邊修正時，請依序問：

1. 這個功能屬於哪個模組的主責任？
2. 這個功能是業務寫入、查詢、治理能力，還是平台能力？
3. 它現在放的位置，是正式設計，還是過渡期實作？
4. 如果它跟原始藍圖不同，是要：
   - 回歸原始藍圖
   - 承認現況並回寫 SDD
   - 拆成新模組
   - 保持子域內部整併

---

## 3. 系統總體架構圖

```mermaid
flowchart TD
    U[使用者 / 管理者 / 客服] --> FE[Frontend\nVue 3 + Pinia + Router + API Client]
    FE --> API[Backend API Layer\nFastAPI Routers / main.py / wiring]
    API --> CORE[Core Platform Layer\ndependencies / scope / features / event_bus / database]

    CORE --> AUTH[auth\n登入 / JWT / identity]
    CORE --> TENANTS[tenants\n公司 / 會員 / entitlement]
    CORE --> ATT[attendance\n打卡 / session / policy / reporting / location]
    CORE --> SCHEDULE[schedule\nshift template / assignment / baseline]
    CORE --> LEAVE[leave\n請假申請 / 審核]
    CORE --> NOTI[notifications\n事件轉通知]
    CORE --> AUDIT[audit\n查詢 / 匯出 / retention]
    CORE --> BACKUP[backup\n公司級備份 / 還原]
    CORE --> CS[customer_service\n客服跨公司 scope]

    AUTH --> DB[(Same DB / Same Tables\ncompany_id Tenant Isolation)]
    TENANTS --> DB
    ATT --> DB
    SCHEDULE --> DB
    LEAVE --> DB
    NOTI --> DB
    AUDIT --> DB
    BACKUP --> DB
    CS --> DB
```

---

## 4. 分層架構圖

```mermaid
flowchart TB
    subgraph Presentation[Presentation Layer]
        FE1[views]
        FE2[router]
        FE3[stores]
        FE4[api client]
    end

    subgraph Application[Application / API Layer]
        AP1[module api routers]
        AP2[main.py]
        AP3[router_wiring.py]
        AP4[startup_wiring.py]
    end

    subgraph Platform[Platform Core Layer]
        C1[dependencies.py\nActor / active_company_id]
        C2[scope.py\nRBAC / scope validation]
        C3[features.py + feature_service.py\nfeature gate]
        C4[event_bus.py\n跨模組事件]
        C5[database.py / config.py / exceptions.py]
    end

    subgraph Domain[Business / Governance Modules]
        D1[auth]
        D2[tenants]
        D3[attendance]
        D4[schedule]
        D5[leave]
        D6[notifications]
        D7[audit]
        D8[backup]
        D9[customer_service]
    end

    FE1 --> AP1
    FE2 --> AP1
    FE3 --> AP1
    FE4 --> AP1
    AP1 --> C1
    AP1 --> C2
    AP1 --> C3
    AP1 --> C4
    AP1 --> C5
    C1 --> D1
    C1 --> D2
    C1 --> D3
    C1 --> D4
    C1 --> D5
    C1 --> D6
    C1 --> D7
    C1 --> D8
    C1 --> D9
```

---

## 5. 模組責任圖

```mermaid
flowchart LR
    AUTH[auth\n登入 / JWT / identity validation]
    TENANTS[tenants\n公司 / members / entitlements / onboarding]
    ATT[attendance\n打卡 / break / session / 工時計算 / policy / reporting / location]
    SCHEDULE[schedule\n班別模板 / 班表指派 / baseline export]
    LEAVE[leave\n請假申請 / 清單 / 審核]
    NOTI[notifications\n事件消費 / 通知記錄]
    AUDIT[audit\n稽核查詢 / 匯出 / retention / purge]
    BACKUP[backup\n單一公司備份 / 還原]
    CS[customer_service\n客服跨公司支援 scope]

    SCHEDULE -->|baseline| ATT
    ATT -->|domain events| NOTI
    AUTH -->|identity| TENANTS
    TENANTS -->|membership / entitlement| ATT
    TENANTS --> LEAVE
    TENANTS --> BACKUP
    TENANTS --> AUDIT
    CS -->|support assignment scope| TENANTS
```

---

## 6. 現況主責任邊界

| 模組 | 主責任 | 不應主導的內容 | 判斷說明 |
|---|---|---|---|
| `auth` | 登入、JWT、身份入口 | 出勤、請假、排班業務 | 所有業務模組只應消費其身份結果 |
| `tenants` | 公司、會員、entitlement、onboarding | 打卡規則、請假判定 | 它是租戶治理與 company source of truth |
| `attendance` | 打卡、session、break、工時、policy、reporting、location | 公司治理、JWT、本體排班 CRUD | 目前最肥大，也是最需要持續切清子域的模組 |
| `schedule` | 班表模板、assignment、baseline | 最終遲到早退判定、實際打卡寫入 | 它定義應該怎麼上班，不定義實際怎麼打卡 |
| `leave` | 請假申請與審核流程 | 出勤工時計算 | 可引用 scope，但不應吸收 attendance 主責任 |
| `notifications` | 事件落地通知 | 主業務決策 | 只消費事件，不反向主導業務語意 |
| `audit` | 稽核查詢、匯出、保留、清除 | 一般業務計算 | 治理模組 |
| `backup` | 公司級資料備份還原 | 一般業務規則判定 | 治理模組 |
| `customer_service` | 客服支援 company scope | 公司內部一般業務流程 | 平台角色治理模組 |

---

## 7. 關鍵互動關係

### 7.1 attendance 與 schedule
- `schedule` 是預期工時與班表來源
- `attendance` 只消費排班 baseline 做政策判定
- 若 `attendance` 開始自己定義第二套班表 normalization，代表邊界失守

### 7.2 attendance 與 notifications
- `attendance` 產生 domain event
- `notifications` 消費事件並落地成可查詢通知
- `notifications` 不應反向決定 `attendance` semantic

### 7.3 auth / tenants / core 與所有模組
- `auth` 提供登入與 token
- `core.dependencies` 建立 actor 與 active company
- `tenants` 提供 company / membership / entitlement 的治理基線
- 其他模組不應自行發明 company scope 規則

---

## 8. 最需要驗證的高風險區

### 8.1 attendance 過胖
目前 `attendance` 同時承擔：
- capture
- reporting
- policy
- location
- 部分 legacy compatibility

這代表它是目前最容易偏離原始藍圖的地方。

### 8.2 reporting 尚未獨立
原始藍圖曾規劃 `reporting` 獨立，但現況仍在 `attendance` 內。

這不是錯，但你之後要判斷：
- 是保留為 attendance 子域
- 還是等規模成熟後再抽成獨立模組

### 8.3 locations 尚未獨立
原始藍圖有 `locations` 想法，但現況 location policy 在 `attendance` 內。

這表示目前 location 比較像出勤的支援子域，而不是獨立業務模組。

---

## 9. 功能驗證時的判斷流程

```mermaid
flowchart TD
    Q1[要驗證的功能是什麼？] --> Q2{屬於哪個主模組責任？}
    Q2 -->|attendance| A1[先看 attendance 主文件與子文件]
    Q2 -->|schedule| A2[看 schedule.md]
    Q2 -->|tenants/auth| A3[看治理與身份相關文件]
    Q2 -->|治理支援| A4[看 audit / backup / notifications / customer_service]

    A1 --> Q3{它是原始規劃內的獨立模組能力嗎？}
    A2 --> Q3
    A3 --> Q3
    A4 --> Q3

    Q3 -->|是| R1[判斷要回歸藍圖、維持子域、或拆模組]
    Q3 -->|否| R2[視為現況正式設計，回寫 SDD 即可]
```

---

## 10. 與其他文件的關係

這份文件搭配以下文件一起使用：

- `SA/architecture/SYSTEM_SDD.md`
- `SA/architecture/MODULE_BOUNDARY_MATRIX.md`
- `SA/architecture/PLANNED_VS_IMPLEMENTED_MATRIX.md`
- `SA/modules/*.md`

其中：
- 這份文件負責「圖像化理解」
- `PLANNED_VS_IMPLEMENTED_MATRIX.md` 負責「原始藍圖 vs 現況落地對照」
- `SYSTEM_SDD.md` 負責「正式敘述版設計說明」
- `modules/*.md` 負責「模組級實作與開發判斷」
