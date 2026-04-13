# SA 文件總覽

> 目的：把 `/opt/attendance-system/SA` 整理成 **唯一可維護的正式架構文件區**，讓人與 AI 都能直接依此開發，不再回頭依賴零散 `docs/` 或重複檔案。

---

## 1. 單一權威原則

從現在起，`SA/` 的**正式開發入口**以這一套核心結構為主：

```text
SA/
├── README.md
├── architecture/
│   ├── SYSTEM_SDD.md
│   ├── MODULE_BOUNDARY_MATRIX.md
│   └── PLANNED_VS_IMPLEMENTED_MATRIX.md
├── governance/
│   ├── DOCUMENTATION_GOVERNANCE.md
│   ├── MODULE_SPEC_TEMPLATE.md
│   └── MODULE_INTAKE_TEMPLATE.md
├── modules/
│   ├── README.md
│   ├── attendance.md
│   ├── attendance-capture.md
│   ├── attendance-reporting.md
│   ├── attendance-policy.md
│   ├── auth.md
│   ├── schedule.md
│   ├── tenants.md
│   ├── leave.md
│   ├── notifications.md
│   ├── audit.md
│   ├── backup.md
│   ├── customer_service.md
│   └── frontend.md
├── SDD學習文件.md
├── SDD_PROGRESS_TRACKER.md
└── legacy-import/
    └── README.md
```

### 正式文件分工

- `architecture/SYSTEM_SDD.md`
  - 系統級架構、核心原則、主要流程、跨模組關係
- `architecture/MODULE_BOUNDARY_MATRIX.md`
  - 模組責任、依賴方向、禁止事項、邊界矩陣
- `architecture/PLANNED_VS_IMPLEMENTED_MATRIX.md`
  - 已規劃與已落地能力的對照與差距追蹤
- `governance/DOCUMENTATION_GOVERNANCE.md`
  - 文件回寫規範
- `governance/MODULE_SPEC_TEMPLATE.md`
  - 模組 / 子域 spec 模板，作為未來 spec-kit 接軌基底
- `governance/MODULE_INTAKE_TEMPLATE.md`
  - 模組需求輸入模板，讓你先整理需求再交給 AI 生成 SDD
- `modules/*.md`
  - 各模組與子域的開發導向 Spec / SDD
- `SDD學習文件.md`
  - 長期參考的 SDD 實戰學習與操作指南
- `SDD_PROGRESS_TRACKER.md`
  - SDD / remediation 狀態總追蹤
- `legacy-import/`
  - 僅保留歷史來源與追溯說明，不是現況權威

> `SA/` 根目錄目前仍保留一些 baseline / 拆解 / 索引輔助文件。  
> 這些可作為整理過程參考，但**正式開發判準仍以 `architecture/`、`governance/`、`modules/` 與 tracker 為主**。

---

## 2. 建議閱讀順序

### 系統級理解
1. `SA/README.md`
2. `SA/SDD學習文件.md`
3. `SA/architecture/SYSTEM_SDD.md`
4. `SA/architecture/MODULE_BOUNDARY_MATRIX.md`
5. `SA/architecture/PLANNED_VS_IMPLEMENTED_MATRIX.md`
6. `SA/governance/DOCUMENTATION_GOVERNANCE.md`
7. `SA/governance/MODULE_SPEC_TEMPLATE.md`
8. `SA/governance/MODULE_INTAKE_TEMPLATE.md`
9. `SA/SDD_PROGRESS_TRACKER.md`

### 開發某個模組前
1. 先讀上面 9 份
2. 再讀對應模組文件，例如：
   - `SA/modules/attendance.md`
   - `SA/modules/attendance-capture.md`
   - `SA/modules/attendance-reporting.md`
   - `SA/modules/attendance-policy.md`
   - `SA/modules/schedule.md`
   - `SA/modules/auth.md`

---

## 3. 與 `docs/` 的關係

`docs/` 不再作為正式設計文件區。

### `docs/` 現在的角色
- 歷史架構版本與舊規格快照
- remediation / audit / fix spec / execution report
- 工作票過程文件
- 供追溯用的舊版基線，例如 SA2.1

原則：
- `docs/` 僅供歷史追溯與來源比對
- 不再作為現況設計判準
- 不再作為新開發的正式依據

### `SA/` 現在的角色
- 目前系統怎麼設計
- 每個模組該放什麼功能
- 邊界怎麼切
- 哪些契約不可破壞
- 未來開發要看哪一份
- 未來導入 spec-kit 前的標準 spec 基線

簡單說：

- `docs/` = 歷史與過程
- `SA/` = 現況與正式開發基線

---

## 4. 目前已完成的整理方向

### 4.1 已完成
- Attendance 模組文件已擴成完整開發版：`SA/modules/attendance.md`
- Attendance 已拆成子文件：
  - `SA/modules/attendance-capture.md`
  - `SA/modules/attendance-reporting.md`
  - `SA/modules/attendance-policy.md`
- 已建立模組 spec 模板：`SA/governance/MODULE_SPEC_TEMPLATE.md`
- 已建立模組需求 intake 模板：`SA/governance/MODULE_INTAKE_TEMPLATE.md`
- 已建立 SDD 操作學習文件：`SA/SDD學習文件.md`
- 已建立 SDD 狀態追蹤檔：`SA/SDD_PROGRESS_TRACKER.md`
- `attendance-capture.md` 與 `schedule.md` 已升級成正式 spec 化範例
- SA 內重複的舊版編號文件已大幅清理，避免 AI 同時讀到多套互相衝突的說法
- 正式文件入口已收斂到 `architecture/`、`modules/`、`governance/` 與 tracker

### 4.2 目前最重要的使用原則
- 不要再把新設計寫回舊 `docs/`
- 不要再同時維護兩套 SA 文件
- 若修 attendance，先讀 `SA/modules/attendance.md`
- 若是交易寫入流程，優先讀 `SA/modules/attendance-capture.md`
- 若牽涉跨模組邊界，先讀 `SA/architecture/MODULE_BOUNDARY_MATRIX.md`
- 若在規劃功能而非直接寫 code，先看 `SA/governance/MODULE_INTAKE_TEMPLATE.md`
- 若怕踩到既有 remediation / canonical contract，先看 `SA/SDD_PROGRESS_TRACKER.md`

---

## 5. 開發前必讀規則

若你或 AI 準備修改系統，至少先回答這五題：

1. 這個功能屬於哪個模組？
2. 它是交易寫入、查詢報表、還是政策判定？
3. 有沒有碰到 tenant / scope / feature gate / boundary owner？
4. 這次要參考哪份 spec？
5. 改完後應該回寫哪一份 `SA/` 文件？

如果這幾題答不出來，不要直接開始改程式。

---

## 6. 未來維護原則

只要發生以下任一情況，就必須更新 `SA/`：

- 新增 API
- 模組責任改變
- 模組邊界改變
- 新增跨模組依賴
- 修改 tenant / scope / feature gate
- 修改 canonical semantic
- 修改 reporting contract
- 修改排班與出勤的整合方式
- 修改 spec metadata / semantic block / validation 流程
- 修改 remediation 判定或風險狀態

---

## 7. 延伸閱讀與實戰入口

如果你要把腦中的模組需求整理成 AI 可讀的正式 SDD，建議這樣讀：

1. `SA/SDD學習文件.md`
2. `SA/governance/MODULE_INTAKE_TEMPLATE.md`
3. `SA/governance/MODULE_SPEC_TEMPLATE.md`
4. `SA/SDD_PROGRESS_TRACKER.md`
5. 對應的 `SA/modules/<module>.md`

建議操作順序：

- 先用 `MODULE_INTAKE_TEMPLATE.md` 整理需求
- 再用 `MODULE_SPEC_TEMPLATE.md` 生成正式 SDD
- 寫 code 前先看 tracker 與模組文件
- 改完後回寫 `SA/`

---

## 8. 給未來 AI 的一句話

> 先讀 `SA/`，再改程式；改完程式，必須回寫 `SA/`。不要再把歷史分析文件當成現況設計文件，也不要跳過 Spec 直接憑感覺改核心模組。
