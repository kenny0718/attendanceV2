# Punch-Out Fix Verification Report

**Date:** 2026-03-10  
**Status:** ✅ Fix Verified  
**Scope:** Verify punch-out timestamp persistence fix before timezone refactor

---

## Step 1 — Backend Punch-Out Logic Verification

### Endpoint: `POST /v1/attendance/punch-out`

**Flow traced:**

```
1. Validate user_id → 400 if missing
2. get_open_session() → 404 if no open session (prevents double punch-out)
3. punch_out_time = datetime.now(timezone.utc)  [UTC time]
4. repo.create_punch(punch_type='out', punch_time=punch_out_time)
5. Calculate duration_minutes
6. repo.close_session(
     punch_out_time=punch_out_time,
     duration_minutes=duration_minutes,
     policy_id=...
   )
   → session.punch_out_time = punch_out_time
   → session.status = 'closed'
   → db.commit()  [atomically written]
   → db.refresh(session)
7. Return PunchOutResponse with session.punch_out_time
```

**Verification results:**

| Check | Result |
|-------|--------|
| `punch_out_time` written on success | ✅ Yes, via `repo.close_session()` |
| `status` changes `open → closed` | ✅ Yes |
| `punch_out_time` returned in response | ✅ Yes, in `PunchOutResponse` |
| Any branch where `punch_out_time` becomes null | ✅ None — only branch is 404 (no open session) |
| `db.commit()` called before response | ✅ Yes, in `close_session()` |
| Closed sessions immutable | ✅ `get_open_session()` only returns `status='open'`, closed sessions cannot be reopened |
| Double punch-out rejected | ✅ Second call gets 404 (no open session) |

**Conclusion:** Backend punch-out logic is correct and safe. ✅

---

## Step 2 — Frontend State Handling Verification

### Root Cause (confirmed)

Original `fetchTodayStatus()` in `attendance.js`:
- Called after every `punch()` success
- When session is `closed`, `getCurrentStatus()` returns `has_open_session=false`
- Original else branch **immediately cleared all state including `punch_out`**

### Fix Applied

`fetchTodayStatus()` else branch now:
1. Calls `getHistory({ limit: 1 })` to get latest session
2. Checks if session is from today using:
   ```js
   const isTodaySession = punchInDate.isSame(today) 
     || (punchOutDate && punchOutDate.isSame(today))
   ```
   *(supports cross-midnight sessions)*
3. Uses today's session data including `punch_out_time`
4. Only clears state if truly no today's record

### Display Components

| Location | Field | Display Logic |
|----------|-------|---------------|
| `Home.vue:16` | `formattedTodayStatus.punch_out` | `StatusCard` value |
| `Home.vue:17` | `todayStatus.punch_out` | Controls `active/empty` CSS class |
| `Home.vue:51` | `todayStatus.punch_out` | `completed` CSS class on button |
| `Home.vue:60` | `todayStatus.punch_out` | `v-if` for ✓ badge |

**No `v-if` that destroys the status section** — all conditionals are on badge/class level only. ✅

### Data Flow After Fix

```
User clicks 下班打卡
  ↓
punch('OUT')
  ↓ API success
todayStatus.punch_out = response.punch_out_time  [displayed immediately ✅]
  ↓
fetchTodayStatus()
  ↓
getCurrentStatus() → has_open_session=false
  ↓
getHistory({ limit:1 }) → sessions[0] = today's closed session
  ↓
isTodaySession = true
  ↓
todayStatus.punch_out = latestSession.punch_out_time  [preserved ✅]
```

**Page refresh flow:**
```
onMounted → fetchTodayStatus()
  ↓
getCurrentStatus() → has_open_session=false
  ↓
getHistory({ limit:1 }) → today's closed session
  ↓
todayStatus.punch_out = session.punch_out_time  [shown on refresh ✅]
```

---

## Step 3 — Regression Checklist

### State Dependencies Scanned

| Logic | Location | Status |
|-------|----------|--------|
| `canPunchOut` | `attendance.js:48` | `is_punched_in && !punch_out` → correct, prevents double punch-out ✅ |
| `canBreakOut` | `attendance.js:49` | `is_punched_in && !punch_out` → correct ✅ |
| `canBreakIn` | `attendance.js:50` | `is_on_break` → unaffected by fix ✅ |
| `canPunchIn` | `attendance.js:47` | `!is_punched_in` → unaffected by fix ✅ |
| Break punch flow | `attendance.js:104-131` | `punchWithLocation()` separate path, unaffected ✅ |
| Punch-in flow | `attendance.js:83-90` | Separate `case 'IN'`, unaffected ✅ |
| `fetchRecentLogs` | `attendance.js:495` | Independent of `punch_out` logic ✅ |
| `loadBreakPunches` | `attendance.js:273` | Independent, break punches unaffected ✅ |
| `formattedTodayStatus` getter | `attendance.js:57-64` | Pure computed from state, no side effects ✅ |

### Call Frequency After Punch-Out

```
punch('OUT') success:
  1. fetchTodayStatus()  ← once only
  2. fetchRecentLogs()   ← once only
  [NOT triggered again — no watcher, no interval]
```

### Stale State Check

- After punch-out: `is_punched_in=false`, `is_on_break=false`, `punch_out` has value ✅
- After page refresh: same state restored from API ✅
- Next day: `isTodaySession` check returns false → state correctly clears ✅

---

## Step 4 — Manual QA Test Scenarios

### 1️⃣ Normal Workday

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | 點擊「上班打卡」 | 上班時間顯示，下班時間顯示 `-` |
| 2 | 點擊「下班打卡」 | 下班時間立即顯示，不消失 |
| 3 | 等待 2 秒 | 下班時間持續顯示 |
| 4 | DevTools Console | 確認 `[FINAL_TODAY_STATUS_SET]` 中 `punch_out` 有值 |

### 2️⃣ Page Refresh After Punch-Out

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | 下班打卡成功後 | 確認下班時間顯示 |
| 2 | 重新整理頁面 (F5) | 上班時間仍顯示 |
| 3 | 重新整理後 | 下班時間仍顯示 |
| 4 | DevTools Console | `[TODAY_MATCH_CHECK] isTodaySession = true` |

### 3️⃣ Break Flow

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | 上班打卡 | 上班時間顯示 |
| 2 | 外出打卡（含原因） | 外出中 badge 顯示 |
| 3 | 返回打卡 | 外出中 badge 消失 |
| 4 | 下班打卡 | 下班時間顯示，不消失 |
| 5 | 重新整理 | 上下班時間均顯示 |

### 4️⃣ Double Punch-Out Prevention

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | 下班打卡成功 | 下班時間顯示 |
| 2 | 再次點擊下班打卡 | 按鈕為 disabled 狀態（`canPunchOut=false`） |
| 3 | 直接 API 呼叫第二次 punch-out | HTTP 404 `NO_OPEN_SESSION` |

### 5️⃣ Cross-Midnight Session (Edge Case)

| Step | Action | Expected Result |
|------|--------|-----------------|
| 1 | 昨天 23:00 上班（不下班） | Open session 持續 |
| 2 | 今天 08:00 下班打卡 | `punch_out_time` 是今天 |
| 3 | `isTodaySession` 判斷 | `punchOutDate.isSame(today)=true` → 顯示 ✅ |

---

## Step 5 — Restore Point

See git tag: `attendance-stable-before-timezone-refactor`

---

## Step 6 — Final Summary

### Punch-Out Fix Status

| Area | Status | Notes |
|------|--------|-------|
| Backend punch-out logic | ✅ Verified | `close_session()` atomically commits |
| Frontend `fetchTodayStatus()` | ✅ Fixed | Now uses `getHistory()` fallback + cross-midnight support |
| `punch_out_time` display | ✅ Correct | `formattedTodayStatus` getter + `StatusCard` |
| Regression: punch-in flow | ✅ Unaffected | Separate code path |
| Regression: break flow | ✅ Unaffected | Separate `punchWithLocation()` path |
| Regression: canPunchOut | ✅ Correct | Disabled after punch-out |
| Regression: page refresh | ✅ Fixed | `onMounted` now shows today's data |
| Cross-midnight edge case | ✅ Fixed | `punchOutDate.isSame(today)` check added |

### Safe to Proceed to Timezone Refactor?

✅ **Yes** — with the following notes:

1. The `punch_out_time` display issue is resolved
2. Debug `console.log` calls should be removed before timezone refactor (or as part of it)
3. Timezone refactor should standardize `datetime.now(timezone.utc)` vs `get_current_time()` discrepancy in backend
4. `dayjs` timezone plugin should be added for robust cross-midnight handling in Taiwan timezone
