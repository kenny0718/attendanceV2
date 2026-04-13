# Platform and SaaS（平台與 SaaS 共通能力）

> 這份文件拆出平台級與 `SaaS`（軟體即服務）共通能力。  
> 目的是讓你確認：除了業務功能之外，這套系統還需要哪些平台能力才能成立。

---

## 1. 這份在看什麼

這份不是在看打卡流程本身，
而是在看這些事情：

- 怎麼登入
- 怎麼判斷你屬於哪家公司
- 誰可以操作哪些公司
- 功能能不能分級
- 高風險操作怎麼追蹤
- 單公司備份 / 還原怎麼做

---

## 2. `Auth / Identity`（身分驗證 / 身分識別）

## 2.1 要有什麼功能
- `login`（登入）
- `password verification`（密碼驗證）
- `JWT issuance`（JWT 權杖發放）
- `login identity validation`（登入身分驗證）
- `platform user`（平台使用者）與 `company scope`（公司操作範圍）的對接

## 2.2 白話理解

> `auth`（身分驗證）負責回答「你是誰」，但不直接等於「你這次能操作哪家公司」。

---

## 3. `Scope Validation`（操作範圍驗證）

## 3.1 要有什麼功能
- 驗證 `user`（使用者）是否屬於某 `company`（公司）
- 驗證 `customer_service`（客服）是否有 `assignment`（被指派關係）
- 驗證 `super_admin`（超級管理員）是否可全域操作
- 驗證公司內角色是否符合權限

## 3.2 白話理解

> `auth`（身分驗證）先確認你是誰，`scope`（作用範圍）再確認你能不能進這家公司做這件事。

---

## 4. `Role Model`（角色模型）

平台至少要考慮：
- `super_admin`（超級管理員）
- `customer_service`（客服 / 客服支援角色）
- `company_user`（公司使用者）

公司內部還可能再拆：
- `admin`（管理者）
- `hr_manager`（HR 管理）
- `employee`（員工）

白話講：

> 不同角色不只是畫面不同，而是 `scope`（操作範圍）、可見資料、可操作資料都不同。

---

## 5. `Feature Flags / Entitlements`（功能開關 / 功能授權）

## 5.1 要有什麼功能
- 公司是否可用某功能
- 不同方案可開不同 `feature`（功能）
- `API`（介面）執行時要先過 `feature gate`（功能閘門 / 功能授權檢查）

## 5.2 白話理解

> `SaaS` 不是每家公司都一定開同樣功能，所以要能控功能開關。

---

## 6. `Audit / Governance`（稽核 / 治理）

## 6.1 要有什麼功能
- 高風險操作要記錄
- 可追查誰做了什麼
- 支援查詢 / 匯出 / `retention`（保存政策）

## 6.2 特別重要的操作
- `pairing code`（配對碼）產生
- 重置密碼
- 撤銷裝置
- 可能影響 `company scope`（公司操作範圍）的設定變更

白話講：

> 不只是功能做得到，還要知道是誰做的，之後才能追責或排查。

---

## 7. `Backup / Restore`（備份 / 還原）

## 7.1 要有什麼功能
- 單一公司匯出
- 單一公司還原
- 不污染其他公司

## 7.2 額外前置檢查
- `Company consistency check`（公司一致性檢查）
- `FK closure check`（外鍵閉包檢查 / 關聯完整性檢查）

白話講：

> `restore`（還原）不是把資料塞回去就好，而是要保證不混租戶、不斷引用。

---

## 8. `Customer Service Scope`（客服操作範圍）

## 8.1 要有什麼功能
- 客服只能操作被指派公司
- 客服不是全域萬能角色
- 高風險操作需稽核

白話講：

> 客服可以跨公司，但不是無限制跨公司。

---

## 9. `API Error Handling`（API 錯誤處理）

建議基線：
- `schema error`（資料結構錯誤）→ `422`
- `business rule / system rule`（業務規則 / 系統規則不允許）→ `400`

白話講：

> 要區分「資料格式錯」和「規則不允許」，不然前後端會很亂。

---

## 10. 你目前看這份時，最需要確認什麼

你只要先確認下面幾題：

1. 你要不要採用 `platform-first identity`（平台優先身份）？
2. 你要不要把 `auth`（身分驗證）跟 `scope`（操作範圍）分開看？
3. 你要不要有 `feature flags / entitlements`（功能開關 / 功能授權）？
4. 你要不要把 `backup / restore`（備份 / 還原）當 `SaaS` 核心能力？
5. 你要不要讓 `customer_service`（客服）僅限 `assignment scope`（被指派的操作範圍）？

---

## 11. 下一步會接到哪裡

這份確認完之後，下一份建議看：

- `SA/sa21-baseline/attendance-domain.md`

因為那份會開始接你最核心的業務域：
- `attendance`（出勤）
- `locations`（地點）
- `location policy`（地點限制規則）
- `trusted device / pairing`（信任裝置 / 裝置配對）
