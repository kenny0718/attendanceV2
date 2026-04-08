Title: Module Spec Template
Author: Johnny Lee
Version: 1.0
Date Created: 2026-04-08
Last Modified: 2026-04-08
spec:id: template.module.base.v1
status: active
scope: SA module / subdomain specification template
source_of_truth: SA/governance/MODULE_SPEC_TEMPLATE.md
---

# 模組 / 子域 Spec 模板

> 用途：這是 `attendance-system` 專案未來所有模組文件、子域文件要共用的標準模板。  
> 目標不是把文件寫得很漂亮，而是讓 **人與 AI 都能用同一格式開發、驗證、回寫文件**。

---

## 1. 使用規則

### 1.1 什麼情況要用這份模板

當你要新增以下任一文件時，應優先套用本模板：

- 新模組 Spec
- 舊模組重寫成正式 Spec
- 大模組底下的子域 Spec
- 高風險流程的專用開發規格

### 1.2 這份模板要解決什麼問題

- 文件格式不一致
- AI 每次都用不同方式描述模組
- 同一功能不知道該放哪裡
- 文件無法支援 spec-driven development
- 做完程式後不知道該如何驗證與回寫

### 1.3 套用原則

1. 先寫現況，不寫理想架構
2. 先寫可驗證規則，再寫抽象描述
3. 一份 Spec 只負責一個清楚範圍
4. 若是子域 Spec，必須回指主模組 Spec
5. 程式改完後，Spec 要同步更新

---

## 2. Metadata 範本

每份 Spec 開頭都應有這段 metadata。

```text
Title: <Spec Title>
Author: Johnny Lee
Version: 1.0
Date Created: YYYY-MM-DD
Last Modified: YYYY-MM-DD
spec:id: <module-or-subdomain>.<name>.v1
status: draft | active | deprecated
module: <module_name>
subdomain: <subdomain_name_if_any>
source_of_truth: <path>
related_code_paths:
  - <path1>
  - <path2>
```

### 2.1 Metadata 欄位說明

| 欄位 | 用途 | 是否必填 |
|---|---|---|
| `Title` | 文件標題 | 必填 |
| `Author` | 文件維護者 | 必填 |
| `Version` | 文件版本 | 必填 |
| `Date Created` | 建立日期 | 必填 |
| `Last Modified` | 最後修改日期 | 必填 |
| `spec:id` | 唯一識別碼 | 必填 |
| `status` | 目前狀態 | 必填 |
| `module` | 所屬模組 | 建議 |
| `subdomain` | 所屬子域 | 子域文件必填 |
| `source_of_truth` | 權威路徑 | 必填 |
| `related_code_paths` | 對應程式碼位置 | 建議 |

---

## 3. 正文標準章節

每份 Spec 建議使用以下章節結構。

### 3.1 文件定位
- 這份文件是給誰看的
- 什麼情況先看這份
- 它和主模組文件的關係

### 3.2 目的與範圍
- 本文件管什麼
- 本文件不管什麼
- 本文件的責任邊界

### 3.3 核心原則
- 至少列 3~7 條
- 每條都應可被驗證或具體判讀

### 3.4 功能規格
- 功能清單
- 每項功能用途
- 哪些檔案通常會改到

### 3.5 Formalized Semantic Block
- 用 YAML 或表格定義正式語意規則
- 重點是讓 AI 可讀、讓人可核對

### 3.6 開發與驗證流程
- 開發步驟
- 驗證條件
- 測試要點
- 失敗時怎麼判斷

### 3.7 依賴與共用元件
- 可依賴誰
- 不可依賴誰
- 共用 helper / service / core component

### 3.8 Do / Don’t
- 應做什麼
- 不應做什麼
- 最容易踩雷的錯誤

### 3.9 回寫規則
- 哪些情況要更新本文件
- 哪些情況還要同步更新主模組或 architecture 文件

---

## 4. Formalized Semantic Block 範本

下面是一份可直接複製的語意區塊範例。

```yaml
scope:
  module: <module_name>
  subdomain: <subdomain_name>
  responsibility:
    - <responsibility_1>
    - <responsibility_2>
  non_responsibility:
    - <non_responsibility_1>
    - <non_responsibility_2>

contracts:
  tenant_isolation:
    source: actor.active_company_id
    body_override_allowed: false
  write_authority:
    owner: <service_or_repo_or_domain>
    api_direct_db_write: false
  semantic_owner:
    canonical_field: <field_name>
    derived_fields:
      - <field_1>
      - <field_2>

validation_rules:
  - rule: <rule_name>
    description: <what must be true>
    verification: <how to verify>

change_triggers:
  update_spec_when:
    - <trigger_1>
    - <trigger_2>
```

---

## 5. 建議章節骨架

下面這段可以直接複製到新的 Spec 內使用。

```md
## 1. 文件定位
## 2. 目的與範圍
## 3. 核心原則
## 4. 功能規格
## 5. Formalized Semantic Block
## 6. 開發與驗證流程
## 7. 依賴與共用元件
## 8. Do / Don’t
## 9. 回寫規則
```

---

## 6. spec-kit 導入前的相容設計

本模板刻意保留以下欄位，是為了未來導入 `spec-kit` 或其他 spec workflow 工具時更容易接軌：

- `spec:id`
- `status`
- `source_of_truth`
- `related_code_paths`
- `Formalized Semantic Block`
- `change_triggers`

這表示：

- 現在先用 Markdown 就能開始
- 之後若導入工具，不需要整套重寫

---

## 7. 專案內的建議套用順序

### 第一批
- `SA/modules/attendance-capture.md`
- `SA/modules/attendance-reporting.md`
- `SA/modules/attendance-policy.md`

### 第二批
- `SA/modules/schedule.md`
- `SA/modules/tenants.md`
- `SA/modules/auth.md`

### 第三批
- 其餘 supporting modules

---

## 8. 最後原則

> 模板的目的不是增加文件量，而是讓每次開發都有一致的 spec 結構可依循。  
> 若某份文件雖然很長，但不能回答「功能在哪裡、誰能改、怎麼驗證」，那它仍然不是好的 Spec。
