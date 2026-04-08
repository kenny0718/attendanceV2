# Attendance Domain

> 這份文件拆出 attendance 相關的核心業務能力。  
> 目的是讓你聚焦確認：打卡、地點、位置限制、裝置綁定，哪些是你真的要的。

---

## 1. 這份在看什麼

主要看：
- `attendance` 核心語意（出勤模組真正定義什麼叫有效出勤）
- `punch / break` 流程（上班打卡、下班打卡、休息出去、休息回來）
- `location policy`（地點限制規則）
- `trusted device / pairing`（信任裝置 / 裝置配對）
- 舊版留下來的 `location evidence` 概念（位置證據）

白話講：

> 這份是在看「打卡這件事到底怎麼成立」，不是只看畫面按鈕而已。

---

## 2. Attendance 核心能力

## 2.1 基本功能
- `punch in / punch out`：上班打卡 / 下班打卡
- `break out / break in`：休息離開 / 休息回來
- `attendance session lifecycle`：一筆出勤從開始到結束的生命週期
- `duration / work hour calculation`：工時 / 時數計算
- `history query`：歷史紀錄查詢

白話講：

> 這一層就是最基本的出勤操作：今天有沒有上班、什麼時候下班、中間有沒有休息、最後總共工作多久。

## 2.2 核心語意
- `PENDING_APPROVAL` 不參與推導（待審核紀錄不能直接算進正式出勤）
- `PENDING_APPROVAL` 不參與日結（待審核資料不能直接進每日結算）
- 必須有 `APPROVED IN` 才成立出勤（核准的上班打卡才算正式開始）
- attendance 是語意 owner，其他模組不能改壞（出勤規則由 attendance 模組說了算）

白話講：

> attendance 不是只是存打卡紀錄而已，它還在定義「什麼叫成立出勤」。

---

## 3. Locations / Location Policy

## 3.1 要有什麼功能
- `allowed locations` 管理（允許打卡地點管理）
- `GPS / geofence` 規則（GPS 與電子圍欄規則）
- attendance punch 前做 `location policy check`（打卡前先檢查地點是否合法）
- 記錄匹配地點（記錄這次打卡符合哪個地點）

## 3.2 白話理解

> 公司可以設定「哪些地點可以打卡」，不在範圍內就不能過。

## 3.3 後端權威原則
- 前端 `precheck` 只能改善體驗（前端先檢查只是讓使用者早點知道）
- 真正是否允許打卡，要由後端判斷
- 不可信任前端送來的 `location_id`

白話講：

> 前端可以先提醒，但最後能不能打卡成功，要由後端決定，不能只相信手機自己說「我在這裡」。

---

## 4. Trusted Device / Pairing

這塊來自舊版 SA1.7，但如果你未來還想保留裝置綁定概念，就要先確認它是不是你要的。

## 4.1 要有什麼功能
- `pairing code` 用來綁裝置（配對碼）
- pairing code `short-lived`（短時效，例如幾分鐘內有效）
- pairing code `one-time`（一次性使用）
- pairing `scope` 綁 `company_id + site_id`（只對某公司、某地點有效）

## 4.2 白話理解

> 配對碼是裝置綁定工具，不是每日打卡合法性的唯一證明。

也就是：
- 它可以幫你認出這台手機 / 裝置是不是先前綁定過
- 但不能因為綁定過，就完全不用看地點、時間、規則

---

## 5. SSID / Location Evidence

這塊也是舊版留下來的概念。

## 5.1 可能要保留的規則
- `wifi_ssid` 可作為 `location evidence`（位置證據）
- 但通常不應成為唯一出勤依據
- 若只有 SSID 命中、沒有 GPS、也不是 trusted device，預設進 `PENDING_APPROVAL`

白話講：

> SSID 比較像輔助證據，不該預設當成最終判定。

也就是說：
- 手機連到公司 Wi-Fi，不代表一定人就在合法打卡位置
- 所以 SSID 可以當參考，但不要直接當唯一依據

---

## 6. attendance 與其他模組邊界

這份先固定幾個很重要的邊界：

- `leave` 不能改壞 attendance semantic（請假模組不能反過來定義出勤）
- `accrual` 不能改壞 attendance semantic（額度 / 補休模組不能反過來定義出勤）
- `dispatch` 不能改壞 attendance semantic（派工模組不能改出勤成立規則）
- `reporting` 不能擁有 attendance 核心規則（報表只能看結果，不能定義結果）

白話講：

> 別的模組可以讀 attendance、依賴 attendance，但不能反過來偷改它的定義。

---

## 7. 你目前看這份時，最需要確認什麼

你只要先確認下面幾題：

1. 你要不要保留 `PENDING_APPROVAL` / `APPROVED IN` 這套語意？
2. 你要不要 `location policy`（地點限制規則）？
3. 你要不要 `trusted device / pairing`（信任裝置 / 配對）這條線？
4. 你要不要 `SSID` 當輔助證據？
5. 你要不要 attendance 當成核心 `semantic owner`（核心規則 owner）？

---

## 8. 下一步會接到哪裡

這份確認完之後，下一份建議看：

- `SA/sa21-baseline/business-modules.md`

因為那份會把其他模組一次整理出來給你選擇。
