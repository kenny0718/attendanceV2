Title: Upstream / Streaming Integration Spec
Author: Johnny Lee
Version: 1.0
Date Created: 2026-04-09
Last Modified: 2026-04-09
spec:id: upstream.streaming.module.v1
status: active
module: upstream_streaming
source_of_truth: SA/modules/upstream-streaming.md
related_code_paths:
  - backend/app/core/event_bus.py
  - backend/app/main.py
  - backend/app/modules/debug_event_api.py
  - backend/app/modules/notifications/event_handlers.py
  - frontend/src/api/client.js
  - frontend/src/api/attendance.js
---

# Upstream / Streaming 正式模組 SDD

> 本文件定義系統未來所有 `upstream`、`streaming`、`SSE`、provider adapter、consumer append 流程的正式 owner 與實作邊界。  
> 目的不是宣稱目前系統已經有完整串流能力，而是把「現在沒有、但接下來要開始做」的 transport owner、contract、模組責任、開工順序先正式定義好，避免之後又把第三方整合直接塞進 `attendance`、`frontend` 或 `notifications`。

---

## 1. 文件定位

### 1.1 這份文件是給誰看的

- 接下來要開始實作第三方 upstream 整合的你
- 要在前端接 `SSE` / streaming consume 的你
- 要 review transport owner、retry、auth、event mapping 的你
- 協助你產 code 的 AI

### 1.2 什麼情況要先看這份

- 你要新增第三方 HTTP upstream client
- 你要新增 webhook / provider callback 驗證層
- 你要新增 `SSE` / `text/event-stream` response path
- 你要在前端做 append-style consume 或 live status stream
- 你要把 domain event 映射成對外 provider contract
- 你不確定 streaming 應該放 `core`、`frontend`、還是某個業務模組

### 1.3 它和其他文件的關係

- 系統總覽：`SA/architecture/SYSTEM_SDD.md`
- 模組邊界：`SA/architecture/MODULE_BOUNDARY_MATRIX.md`
- 前端模組：`SA/modules/frontend.md`
- 通知消費者：`SA/modules/notifications.md`
- 模板來源：`SA/governance/MODULE_SPEC_TEMPLATE.md`

### 1.4 一句話理解

> `upstream_streaming` 是平台整合與串流傳輸 owner，不是任何單一業務模組的附屬 helper。

---

## 2. 目的與範圍

### 2.1 本文件負責的範圍

`upstream_streaming` 模組負責：

- 對外 upstream HTTP client owner
- provider adapter / webhook 驗證入口
- `SSE` response path owner
- 串流事件 envelope 與 append contract
- transport retry / timeout / auth header / observability 基線
- internal domain event 與 external transport event 的 mapping 邊界
- frontend streaming consumer contract

### 2.2 本文件不負責的範圍

這個模組不負責：

- attendance canonical semantic owner
- auth / tenants / leave 的 domain rule owner
- 將 internal EventBus 直接升格成 external stream protocol
- 前端畫面最終展示內容的業務語意決策
- notifications 查詢資料模型
- 用 streaming 取代既有所有 REST API

### 2.3 目前真實 code baseline（2026-04-09）

目前程式現況已確認：

- `frontend/src/api/client.js` 只有 `axios.create()` request/response client，沒有 `EventSource`、`fetch(stream)`、`ReadableStream`、`WebSocket`
- `frontend/src/api/attendance.js` 全部都是一次性 REST consume，沒有 append-style stream consumer
- `backend/app/core/event_bus.py` 是 in-memory synchronous internal event bus，不是 HTTP upstream client，也不是 `SSE` gateway
- `backend/app/modules/debug_event_api.py` 只有 debug JSON API，沒有 `text/event-stream`
- `backend/app/modules/notifications/event_handlers.py` 是 internal subscriber，不是外部 provider adapter
- `backend/app/main.py` startup 只有 subscriber wiring，沒有 upstream transport wiring

### 2.4 正式結論

> 目前系統**尚未有正式 upstream / streaming owner 實作**；本文件是為了讓後續可以依正式 SDD 直接開工，而不是繼續散落在既有模組內硬接。

---

## 3. 核心原則

| 原則 | 定義 | 可驗證條件 |
|---|---|---|
| Transport Owner First | 先定義 transport owner，再接 provider | 新 upstream 不可直接塞進 `attendance.service` / `auth.service` / `tenants.service` |
| Internal Event ≠ External Stream | internal EventBus 不等於外部串流協定 | 不可把 `event_bus.emit()` 直接當成 `SSE` contract |
| Domain Mapping Before Delivery | 先明確定義 domain event 到 transport event 的映射，再做 deliver | 每個 stream event 都要能指出 semantic owner |
| REST Default, Streaming By Need | 預設先維持 REST；只有明確需要 live append 才新增 streaming | 不可為了「看起來即時」把所有查詢改成串流 |
| Provider Contract Versioned | provider / consumer event payload 必須可版本化 | event name、payload schema、retry 行為需可文件化 |
| Frontend Is Consumer Only | 前端只負責 consume stream，不持有 transport semantic owner | 前端不可自己定義 upstream event 真正語意 |
| Auth / Scope Explicit | 每一條 streaming path 都要明確 auth 與 scope | 不可出現匿名 stream 或靠前端 local state 決定可看事件 |
| Observability Mandatory | upstream / streaming 失敗需可追 | timeout、disconnect、retry、drop 都需有 log / metrics 設計 |

---

## 4. 功能規格

### 4.1 Outbound Upstream HTTP Client

**用途**：系統主動呼叫外部 provider / upstream API。  
**正式 owner**：`backend/app/core` 之下的新 transport 路徑，或新的平台整合模組。  
**不應落點**：`attendance.service`、`auth.service`、`tenants.service` 內直接 `httpx` / `requests`。

**必要行為**：
- 統一 timeout、retry、auth header、base URL
- request / response logging 與 redaction 規則一致
- 失敗類型需可區分：timeout、4xx、5xx、network error
- domain module 只能提供 payload mapping，不直接持有 transport 細節

### 4.2 Inbound Provider Adapter / Webhook

**用途**：接收 provider 主動 callback、webhook、狀態回傳。  
**正式 owner**：`backend` 平台整合入口。

**必要行為**：
- 驗證來源與簽章
- 驗證 event schema
- 將 provider event 轉成 internal normalized event / command
- 不直接在 adapter 內寫複雜業務規則

### 4.3 Server-Sent Events Gateway

**用途**：把後端可公開的 live 狀態，以 `text/event-stream` 形式提供給前端。  
**正式 owner**：`backend` 新 streaming transport layer。  
**非 owner**：`event_bus.py`。

**必要行為**：
- 明確 route owner 與 auth scope
- 定義 event name、event id、data payload
- 定義 keepalive / disconnect / reconnect 語意
- 只暴露可公開的 stream topic，不把 internal debug event 直接外送

### 4.4 Frontend Streaming Consumer

**用途**：前端用 `EventSource` 或其他正式 streaming consume 路徑接收增量事件。  
**正式 owner**：`frontend/src/api` 下的新 streaming client 與對應 store consume flow。

**必要行為**：
- 與既有 `axios` client 分離，不混成同一個攔截器假象
- stream event 先進 consumer adapter，再更新 store
- UI append 與 reconnection state 可觀測
- 未正式定義 contract 前，不得直接在 view 內硬寫 `onmessage`

### 4.5 Domain Event Mapping

**用途**：把 `attendance`、`leave`、`notifications` 等 domain 狀態轉成可對外 deliver 的 transport event。  
**正式 owner**：domain module 擁有 semantic mapping；transport 層擁有 delivery。

**必要行為**：
- 每個 transport event 要能追到 semantic owner
- mapping 與 delivery 分層
- event schema 改變時，必須同步更新 provider / consumer SDD

### 4.6 Delivery Reliability / Observability

**用途**：讓 upstream / streaming 在失敗時可追、可重試、可判斷。  
**正式 owner**：transport layer。

**必要行為**：
- timeout 與 retry 策略明確
- log 不可洩漏敏感 token / payload
- stream disconnect、reconnect、drop 需可追蹤
- 若未做 durable queue，就要在文件中明說 at-most-once / best-effort 限制

---

## 5. 建議實作落點（可直接開工）

### 5.1 Backend 建議目錄

第一版建議建立：

- `backend/app/core/upstream/`
  - `client.py`：對外 HTTP client factory / shared config
  - `contracts.py`：provider request/response envelope 定義
  - `exceptions.py`：transport error 分類
  - `observability.py`：logging / metrics helper
- `backend/app/core/streaming/`
  - `schemas.py`：SSE envelope schema
  - `service.py`：stream topic 組裝與 publish adapter
  - `api.py`：`text/event-stream` route
  - `auth.py`：stream auth / scope helper

### 5.2 Frontend 建議目錄

第一版建議建立：

- `frontend/src/api/streaming.js`
  - `createEventSource()`
  - topic subscribe helper
  - reconnect policy
- `frontend/src/stores/<target>.js`
  - consume normalized stream event
- `frontend/src/composables/`
  - 必要時做 stream lifecycle hook

### 5.3 第一批開工順序

1. 先做 backend transport owner 骨架
2. 再做單一 `SSE` route proof-of-contract
3. 再做 frontend `EventSource` consumer adapter
4. 最後才接 domain mapping 與實際業務 UI

### 5.4 第一批不要做的事

- 不要一開始就做通用 message broker 抽象層
- 不要把 internal EventBus 直接包成外部 `SSE`
- 不要先做多 provider 再定 contract
- 不要讓 `attendance` 直接依賴第三方 SDK

---

## 6. Formalized Semantic Block

```yaml
scope:
  module: upstream_streaming
  responsibility:
    - outbound_upstream_http_client
    - inbound_provider_adapter
    - sse_gateway
    - frontend_stream_consumer_contract
    - delivery_retry_timeout_auth_observability
    - domain_to_transport_event_mapping_boundary
  non_responsibility:
    - attendance_canonical_semantic_owner
    - auth_domain_rule_owner
    - tenant_source_of_truth
    - notification_read_model_owner
    - converting_internal_event_bus_into_public_protocol

contracts:
  transport_owner:
    backend_owner: app.core.upstream_and_streaming
    frontend_owner: frontend.src.api.streaming
    domain_modules_may_define_mapping_only: true
  streaming_protocol:
    public_sse_allowed: true
    internal_event_bus_is_public_protocol: false
    event_envelope_required: true
  auth_scope:
    jwt_required: true
    anonymous_stream_allowed: false
    tenant_scope_source: actor.active_company_id
  delivery_semantics:
    default_mode: best_effort
    durable_delivery_guaranteed: false
    retry_policy_must_be_explicit: true
  versioning:
    event_name_versioning_required: true
    payload_schema_versioning_required: true

validation_rules:
  - rule: no_direct_domain_http_client_sprawl
    description: 業務模組不可各自直接持有第三方 transport 實作
    verification: upstream code is centralized in transport owner path
  - rule: internal_event_bus_not_exposed_as_sse
    description: internal EventBus 不可直接當 public stream contract
    verification: SSE route uses explicit streaming schema and auth path
  - rule: frontend_consumer_only
    description: frontend 只能 consume，不可成為 semantic owner
    verification: stream schema defined by backend/domain contract, not by views
  - rule: auth_scope_required
    description: 每條 stream path 必須明確驗證 JWT 與 tenant scope
    verification: stream route rejects unauthenticated access
  - rule: observability_defined
    description: retry、timeout、disconnect 必須可追蹤
    verification: transport logs and failure categories are defined

change_triggers:
  update_spec_when:
    - new_upstream_provider_added
    - webhook_contract_changed
    - sse_route_added_or_changed
    - frontend_stream_consumer_added
    - retry_timeout_policy_changed
    - event_envelope_changed
```

---

## 7. 開發與驗證流程

### 7.1 開發步驟

1. 先確認這次需求是 outbound upstream、inbound webhook、還是 public streaming
2. 先定義 provider / consumer contract，不先寫 transport 細節
3. 確認 semantic owner 是哪個 domain module
4. 在 `core/upstream` 或 `core/streaming` 建 transport owner
5. 再讓 domain module 只提供 mapping 與 use-case orchestration
6. 最後才接 frontend consume 與 UI append
7. 改完後同步回寫本文件、`frontend.md`、必要時 architecture 文件

### 7.2 第一版最低驗證清單

#### Backend Transport 驗證
- shared client 可統一 timeout / retry / auth
- 錯誤分類可區分 provider error 與 network error
- 不在 domain service 內直接散落第三方呼叫

#### SSE 驗證
- route 回傳 `text/event-stream`
- 未登入或無 scope 會被拒絕
- event envelope 穩定
- disconnect / reconnect 行為可預測

#### Frontend Consumer 驗證
- 前端有獨立 streaming client
- consume 後更新 store，而不是 view 直接吞 payload
- reconnection 或 stream error 可反映到 state

#### Boundary 驗證
- internal EventBus 未被直接暴露為 public protocol
- domain semantic 與 transport delivery 未混層
- 文件中的 owner 與 code 落點一致

---

## 8. 依賴與共用元件

### 8.1 可依賴

- `app.core.dependencies`
- `app.core.scope`
- `app.core.config`
- domain module 的 normalized event mapping
- frontend store / composable

### 8.2 不應承擔

- attendance / leave / auth 最終業務決策
- company / member source-of-truth 管理
- audit / notification read model
- 臨時 debug event 外送成正式產品能力

### 8.3 與既有模組責任分界

| 模組 | `upstream_streaming` 提供什麼 | 不提供什麼 |
|---|---|---|
| `frontend` | 正式 stream consume contract | 不替 frontend 決定畫面語意 |
| `notifications` | 可消費的 normalized transport / domain event 邊界 | 不替 notifications 持有查詢模型 |
| `attendance` | transport delivery 能力與 mapping 邊界 | 不替 attendance 定義 canonical semantic |
| `core.event_bus` | 可作 internal signal source 之一 | 不直接升格成 public protocol |

---

## 9. Do / Don’t

### Do
- 先定義 owner，再寫 code
- 把 transport / mapping / consume 分層
- 保持 REST 為預設，streaming 只用在明確需要的即時場景
- 把 auth、scope、retry、timeout、observability 寫清楚
- 讓前端只 consume normalized event

### Don’t
- 不要把第三方 SDK 直接埋進業務 service
- 不要把 `event_bus.py` 當成 public streaming 協定
- 不要在 view 內直接成為 event semantic owner
- 不要在沒有 contract 時先做 append UI
- 不要假設串流一定比 REST 好

### 最容易踩雷的錯誤
1. 把 internal event 名稱直接暴露給前端，導致 internal contract 綁死
2. 前端先做 `onmessage`，後端再補 schema，最後雙方語意漂移
3. transport retry / timeout 散落在各 service
4. webhook 驗章、schema 驗證、domain rule 全寫在同一層
5. 以為 notifications subscriber 就等於 upstream adapter

---

## 10. 可直接開工的第一張實作票建議

### Ticket A：Backend Streaming Skeleton
- 建立 `backend/app/core/streaming/`
- 定義 SSE envelope schema
- 建一條 authenticated demo stream route
- 僅輸出最小 heartbeat / status event

### Ticket B：Frontend Streaming Client Skeleton
- 建立 `frontend/src/api/streaming.js`
- 封裝 `EventSource` lifecycle
- 提供 subscribe / close / reconnect 基本行為

### Ticket C：Single Domain Mapping POC
- 選一個低風險 domain status event
- 定義 normalized transport event name v1
- 驗證 backend → frontend append chain

### Ticket D：Outbound Upstream Client Skeleton
- 建立 shared HTTP client
- 定義 timeout / retry / auth header policy
- 用單一 provider sandbox route 驗證 shared transport

---

## 11. 回寫規則

當發生以下任一情況，必須更新本文件：

- 新增 upstream provider
- 新增 webhook / callback path
- 新增 `SSE` route 或變更 event envelope
- 前端新增 streaming consumer
- retry / timeout / auth policy 改變
- internal event 與 external transport event 的 mapping 改變

若影響模組邊界，還要同步更新：

- `SA/modules/frontend.md`
- `SA/modules/notifications.md`（若事件消費契約改變）
- `SA/architecture/SYSTEM_SDD.md`
- `SA/architecture/MODULE_BOUNDARY_MATRIX.md`
- `SA/SDD_PROGRESS_TRACKER.md`
