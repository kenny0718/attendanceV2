# P4_A1 Reporting Growth Audit Report

> **Ticket Type**: Audit
> **Phase**: 4
> **Priority**: Medium
> **Execution Mode**: Read-only / Documentation  
> **Status**: Done

---

## 1. Summary（PASS / PASS WITH NOTES / FAIL）

**PASS WITH NOTES**

本次審計結論為：目前 reporting 模組仍大致維持在 **reporting consumer only** 的邊界內，尚未出現明確的 canonical semantic ownership 轉移，也未看到 reporting 重算或重定義 canonical duration 的證據。

但同時，`backend/app/modules/attendance/api/reporting.py` 已開始承擔多種 reporting 責任，包括：

- endpoint boundary
- query parameter validation
- actor / permission gating
- feature gate
- repo retrieval orchestration
- display enrichment
- response shaping
- summary output normalization

因此，雖然目前仍未達到 FAIL，也尚未觀察到 reporting 已經越界為 semantic owner，但已出現 **growth concentration** 訊號；若未來持續把新報表、summary、export 類能力直接加入 `api/reporting.py`，風險將明顯升高。

本票依據的正式語意基準如下：

- canonical = `session.duration_minutes`（gross）
- reporting = canonical consumer only
- reporting 不得重算 canonical
- reporting 不得重新定義 canonical
- derived values 若存在，必須與 canonical 分離

---

## 2. Files Inspected

### Governance / Semantic Baseline
- `docs/00_AI_GOVERNANCE/CURSOR_EXECUTION_CONTROL.md`
- `docs/00_AI_GOVERNANCE/CURSOR_BACKEND_SAFE_EDIT_RULES.md`
- `docs/00_AI_GOVERNANCE/AI_CONTEXT.md`
- `docs/attendance/architecture/POLICY_ENGINE_FREEZE.md`
- `docs/attendance/architecture/POLICY_ENGINE_GOVERNANCE.md`
- `docs/attendance/architecture/P1_SEMANTIC_DECISION.md`

### Reporting / Attendance Code
- `backend/app/modules/attendance/api/reporting.py`
- `backend/app/modules/attendance/reporting_service.py`
- `backend/app/modules/attendance/reporting_repo.py`
- `backend/app/modules/attendance/repo.py`
- `backend/app/modules/attendance/api.py`
- `backend/app/modules/attendance/service.py`

### Tests
- `backend/app/modules/attendance/tests/test_reporting_sessions.py`
- `backend/app/modules/attendance/tests/test_reporting_user_summary.py`
- `backend/app/modules/attendance/tests/test_reporting_company_summary.py`
- `backend/app/modules/attendance/tests/test_reporting_helpers_boundary.py`

---

## 3. Responsibility Matrix

| responsibility | current owner | 是否合理 | risk |
|---|---|---:|---|
| endpoint boundary | `api/reporting.py` | 是 | Low |
| query parameter handling | `api/reporting.py` + `api.reporting_helpers` | 是 | Low |
| actor / permission gating | `api/reporting.py` | 是 | Low-Medium |
| feature gate | `api/reporting.py` | 是 | Low |
| data retrieval orchestration | `api/reporting.py` → `reporting_repo.py` | 大致合理 | Medium |
| summary aggregation | `reporting_service.py` | 是 | Low |
| canonical field exposure | `api/reporting.py` / `reporting_service.py` | 是 | Low |
| display enrichment | `api/reporting.py` | 合理但偏重 | Medium |
| response shaping / schema adaptation | `api/reporting.py` | 是 | Medium |
| query retrieval boundary | `reporting_repo.py` | 是 | Low |

### 3.1 Responsibility Evidence

#### A. endpoint boundary / parameter boundary / dependency boundary

```42:52:backend/app/modules/attendance/api/reporting.py
@router.get("/sessions", response_model=SessionsListResponse)
def get_sessions(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db),
):
```

#### B. feature gate + datetime validation + query range normalization

```65:71:backend/app/modules/attendance/api/reporting.py
    _require_attendance_feature(actor.active_company_id, db)

    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 100")

    _validate_datetime_range(start_date, end_date)
    start_utc, end_utc = resolve_reporting_query_range_to_utc(start_date, end_date)
```

#### C. actor / permission gating

```73:86:backend/app/modules/attendance/api/reporting.py
    # Scope enforcement
    target_user_id: Optional[UUID] = None
    is_manager = actor.is_admin()

    if user_id is not None:
        try:
            target_user_id = UUID(user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user_id format")
        if not is_manager and target_user_id != actor.user_id:
            raise HTTPException(status_code=403, detail="Employees can only query their own sessions")
    else:
        if not is_manager:
            target_user_id = actor.user_id
```

```196:199:backend/app/modules/attendance/api/reporting.py
    _require_attendance_feature(actor.active_company_id, db)

    if not actor.is_admin():
        raise HTTPException(status_code=403, detail="Company summary requires manager or admin role")
```

#### D. repo retrieval orchestration

```88:106:backend/app/modules/attendance/api/reporting.py
    repo = get_reporting_repository(db)

    sessions = repo.get_sessions_for_reporting(
        company_id=actor.active_company_id,
        user_id=target_user_id,
        start_utc=start_utc,
        end_utc=end_utc,
        status=status,
        limit=limit,
        offset=offset,
    )

    total = repo.count_sessions_for_reporting(
        company_id=actor.active_company_id,
        user_id=target_user_id,
        start_utc=start_utc,
        end_utc=end_utc,
        status=status,
    )
```

#### E. display enrichment + response shaping

```108:123:backend/app/modules/attendance/api/reporting.py
    user_ids = list({str(s.user_id) for s in sessions})
    display_names = get_display_names(db, user_ids)

    items = []
    for s in sessions:
        items.append(SessionResponse(
            session_id=s.id,
            user_id=s.user_id,
            company_id=s.company_id,
            display_name=display_names.get(str(s.user_id)),
            punch_in_time=s.punch_in_time.astimezone(TZ_TAIPEI),
            punch_out_time=s.punch_out_time.astimezone(TZ_TAIPEI) if s.punch_out_time is not None else None,
            status=s.status,
            duration_minutes=s.duration_minutes,
            notes=s.notes,
        ))
```

#### F. summary aggregation owned by reporting_service

```17:56:backend/app/modules/attendance/reporting_service.py
def calculate_user_summary(sessions: List[Any]) -> Dict[str, Any]:
    """Calculate per-user attendance summary from fetched sessions.

    Args:
        sessions: list of AttendanceSession ORM objects (already fetched by repo)

    Returns:
        Plain dict with keys matching UserSummaryResponse fields
        (excluding user_id, which is provided by the router).
    """
    total_sessions = len(sessions)
    closed_sessions = sum(1 for s in sessions if s.status == "closed")
    open_sessions = sum(1 for s in sessions if s.status == "open")

    # canonical duration — duration_minutes IS NULL for open sessions
    total_work_minutes = sum(s.duration_minutes or 0 for s in sessions)

    # average: None when no closed sessions (avoid division by zero)
    average_session_minutes: Optional[float] = (
        total_work_minutes / closed_sessions
        if closed_sessions > 0 else None
    )
```

```59:109:backend/app/modules/attendance/reporting_service.py
def calculate_company_summary(sessions: List[Any]) -> Dict[str, Any]:
    """Calculate company-level attendance summary from fetched sessions.

    Args:
        sessions: list of AttendanceSession ORM objects (already fetched by repo)

    Returns:
        Plain dict with keys matching CompanySummaryResponse fields
        (excluding company_id, which is provided by the router).
    """
    total_sessions = len(sessions)
    closed_sessions = sum(1 for s in sessions if s.status == "closed")
    open_sessions = sum(1 for s in sessions if s.status == "open")

    # 用戶去重（Python set，禁止 SQL COUNT DISTINCT）
    total_users_with_sessions = len(set(s.user_id for s in sessions))

    # canonical duration — duration_minutes IS NULL for open sessions
    total_work_minutes = sum(s.duration_minutes or 0 for s in sessions)
```

#### G. query retrieval boundary owned by reporting_repo

```41:79:backend/app/modules/attendance/reporting_repo.py
    def get_sessions_for_reporting(
        self,
        company_id: str,
        user_id: Optional[UUID] = None,
        start_utc: Optional[datetime] = None,
        end_utc: Optional[datetime] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AttendanceSession]:
        """查詢 sessions（reporting 用途）

        Tenant Isolation: 強制 WHERE company_id = ?
        Date filter: 僅使用 punch_in_time（不使用 punch_out_time）
        索引命中: idx_sessions_company_punch_in (company_id, punch_in_time)
        """
        query = self.db.query(AttendanceSession).filter(
            AttendanceSession.company_id == company_id
        )
```

---

## 4. Growth / Size Findings

### 4.1 `reporting_service.py`

`reporting_service.py` 目前體積小、責任單純，僅承擔 summary aggregation，且檔頭明確標示：

- No DB access
- No repo calls
- No router imports
- No schema imports
- No actor/permission logic

證據如下：

```1:13:backend/app/modules/attendance/reporting_service.py
"""Attendance Reporting — Aggregation Service

Pure aggregation helpers extracted from api/reporting.py (Micro Decomposition Step 3).

Rules:
- No DB access
- No repo calls
- No router imports
- No schema imports
- No actor/permission logic
- Input: already-fetched sessions list
- Output: plain dict with calculated values
"""
```

本檔目前 **未見檔案膨脹**、**未見多責任混雜**、**未見高風險變更集中**。

### 4.2 `api/reporting.py`

`api/reporting.py` 目前只有 3 個 endpoints：

- `/sessions`
- `/reports/user-summary`
- `/reports/company-summary`

但已同時承擔：

- boundary handling
- feature gate
- actor / permission gating
- query validation
- repo orchestration
- display enrichment
- response shaping
- summary output timezone normalization

其中 `/sessions` endpoint 最重，單一路徑已經涵蓋：

- user scope 判定
- repo list fetch
- repo count fetch
- display name lookup
- response DTO mapping
- Taipei timezone shaping

證據如下：

```42:125:backend/app/modules/attendance/api/reporting.py
@router.get("/sessions", response_model=SessionsListResponse)
def get_sessions(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    actor: Actor = Depends(get_actor_with_company),
    db: Session = Depends(get_db),
):
    """GET /api/v1/attendance/sessions — Sessions reporting (WP-11-06 Step 1)
    // ...
    """
    _require_attendance_feature(actor.active_company_id, db)
    // ...
    repo = get_reporting_repository(db)
    // ...
    total = repo.count_sessions_for_reporting(...)
    // ...
    display_names = get_display_names(db, user_ids)
    // ...
    return SessionsListResponse(sessions=items, total=total, limit=limit, offset=offset)
```

### 4.3 Growth Risk Judgment

當前尚未達到「已明確失控」程度，但已出現以下 growth risk：

1. 新 endpoint 很容易繼續往 `api/reporting.py` 累加。
2. 新增 summary / export 時，最可能先膨脹的是 router 層，而非 repo / reporting_service。
3. 變更熱點已偏向 `api/reporting.py`，代表未來高風險修改集中點已出現。

**判定：Growth / Size Risk = Medium**

---

## 5. Query Boundary Findings

### 5.1 Query boundary 整體判斷

目前 reporting 的查詢邊界整體仍然乾淨：

- `api/reporting.py` 不直接寫 SQL
- `reporting_repo.py` 承擔 retrieval / filter / pagination
- `reporting_service.py` 承擔 application-layer aggregation

這種切法整體符合 reporting boundary。

### 5.2 `reporting_repo.py` 邊界

`reporting_repo.py` 目前只處理：

- tenant filter
- user filter
- datetime range filter
- status filter
- order / pagination
- summary session retrieval

未見以下越界責任：

- actor / permission logic
- canonical reinterpretation
- break deduction rule
- business semantic branching
- response shaping

證據如下：

```81:106:backend/app/modules/attendance/reporting_repo.py
    def count_sessions_for_reporting(
        self,
        company_id: str,
        user_id: Optional[UUID] = None,
        start_utc: Optional[datetime] = None,
        end_utc: Optional[datetime] = None,
        status: Optional[str] = None,
    ) -> int:
        """計算 sessions 總數（reporting 用途，供分頁 total 欄位使用）"""
        query = self.db.query(AttendanceSession).filter(
            AttendanceSession.company_id == company_id
        )
```

```108:160:backend/app/modules/attendance/reporting_repo.py
    def get_user_summary_sessions(
        self,
        company_id: str,
        user_id: UUID,
        start_utc: Optional[datetime] = None,
        end_utc: Optional[datetime] = None,
    ) -> List[AttendanceSession]:
        // ...
        return query.order_by(AttendanceSession.punch_in_time.asc()).all()

    def get_company_summary_sessions(
        self,
        company_id: str,
        start_utc: Optional[datetime] = None,
        end_utc: Optional[datetime] = None,
    ) -> List[AttendanceSession]:
        // ...
        return query.order_by(AttendanceSession.punch_in_time.asc()).all()
```

### 5.3 `api/reporting.py` orchestration 負擔

雖然 query 邊界仍乾淨，但 `api/reporting.py` 已承擔部分 query orchestration：

- 先抓 sessions
- 再抓 total count
- 再做 display name lookup
- 再 map 成 response

這種 orchestration 目前仍屬可接受，但已顯示 router 在 reporting flow 中不只是一層薄 boundary。

證據如下：

```88:109:backend/app/modules/attendance/api/reporting.py
    repo = get_reporting_repository(db)

    sessions = repo.get_sessions_for_reporting(
        company_id=actor.active_company_id,
        user_id=target_user_id,
        start_utc=start_utc,
        end_utc=end_utc,
        status=status,
        limit=limit,
        offset=offset,
    )

    total = repo.count_sessions_for_reporting(
        company_id=actor.active_company_id,
        user_id=target_user_id,
        start_utc=start_utc,
        end_utc=end_utc,
        status=status,
    )

    user_ids = list({str(s.user_id) for s in sessions})
    display_names = get_display_names(db, user_ids)
```

### 5.4 Boundary Judgment

- `reporting_repo.py`：乾淨
- `reporting_service.py`：乾淨
- `api/reporting.py`：仍可接受，但 orchestration weight 已上升

**判定：Query Boundary = Clean with Notes**

---

## 6. Business Logic Leakage Findings

### 6.1 Canonical reinterpretation

未發現 reporting 對 canonical duration 進行重新定義。

`reporting_service.py` 直接使用 `s.duration_minutes` 聚合總工時：

```31:37:backend/app/modules/attendance/reporting_service.py
    # canonical duration — duration_minutes IS NULL for open sessions
    total_work_minutes = sum(s.duration_minutes or 0 for s in sessions)

    # average: None when no closed sessions (avoid division by zero)
    average_session_minutes: Optional[float] = (
        total_work_minutes / closed_sessions
        if closed_sessions > 0 else None
```

```76:88:backend/app/modules/attendance/reporting_service.py
    # canonical duration — duration_minutes IS NULL for open sessions
    total_work_minutes = sum(s.duration_minutes or 0 for s in sessions)

    # average per session: None when no closed sessions
    average_minutes_per_session: Optional[float] = (
        total_work_minutes / closed_sessions
        if closed_sessions > 0 else None
    )
```

這符合 semantic baseline：reporting 直接消費 persisted canonical field，而非自建新的 canonical meaning。

### 6.2 Derived metric calculation

目前 reporting 有 derived metrics，但都屬於 summary 聚合層的合理衍生值：

- `average_session_minutes`
- `average_minutes_per_session`
- `average_minutes_per_user`

這些 derived values 是從 canonical total 派生，沒有取代 canonical 欄位，也沒有回寫 semantic authority。

### 6.3 Actor-based semantic branching

未發現 actor 角色會改變 reporting 的 duration semantics。

目前 actor 只影響：

- 是否可查自己以外的 user sessions
- 是否可查 company summary

而不影響：

- canonical 欄位定義
- total_work_minutes semantics
- summary aggregation semantics

因此未見 actor-based semantic branching。

### 6.4 Business rules that belong elsewhere

本次 inspected reporting code 中，未見以下責任落入 reporting：

- policy rule evaluation
- missing segment rule
- break deduction rule
- close-flow business ownership
- canonical persistence ownership

相對地，這些仍位於非 reporting 路徑。例如 `service.py` 中的 punch-out close orchestration：

```214:239:backend/app/modules/attendance/service.py
    def build_punch_out_policy_evaluation(
        self,
        session,
        repo,
        company_id: str,
        user_id: UUID,
        punch_out_time: datetime,
        gross_minutes: int,
    ) -> PolicyEvalPayload:
        """Punch-out close flow orchestration entry with internal dry-run hook."""
        missing_input = self._build_missing_segment_input(
            session=session,
            repo=repo,
            company_id=company_id,
            user_id=user_id,
            punch_out_time=punch_out_time,
        )
        missing_result = evaluate_missing_segment_dry_run(missing_input)
```

**判定：未見 reporting 成為 semantic owner / orchestration owner。**

---

## 7. Canonical Contract Findings

### 7.1 Formal contract baseline

正式文件明確規定：

```47:63:docs/attendance/architecture/P1_SEMANTIC_DECISION.md
Canonical ownership is fixed as follows:

- **Owner**: punch-out close-flow orchestration
- **Calculation source**: `work_hour_engine`
- **Repository role**: persistence only
- **Policy role**: consumer only
- **Reporting role**: consumer only
```

```125:139:docs/attendance/architecture/P1_SEMANTIC_DECISION.md
## 6. Reporting Contract

Reporting is governed by the following contract:

1. Reporting **must directly use** canonical duration from `session.duration_minutes` when referencing canonical duration.
2. Summary logic **must not recalculate canonical duration** from raw punches, break punches, or alternative formulas.
3. Reporting **must not reinterpret** canonical duration as net duration.
4. Derived values, if shown, **must be presented in separate fields or separate columns** from canonical duration.
5. Reporting totals that represent canonical duration **must aggregate the persisted canonical field**.
```

### 7.2 Implementation check

#### A. session list 直接暴露 persisted canonical field

```111:123:backend/app/modules/attendance/api/reporting.py
    items = []
    for s in sessions:
        items.append(SessionResponse(
            session_id=s.id,
            user_id=s.user_id,
            company_id=s.company_id,
            display_name=display_names.get(str(s.user_id)),
            punch_in_time=s.punch_in_time.astimezone(TZ_TAIPEI),
            punch_out_time=s.punch_out_time.astimezone(TZ_TAIPEI) if s.punch_out_time is not None else None,
            status=s.status,
            duration_minutes=s.duration_minutes,
            notes=s.notes,
        ))
```

#### B. summary 直接聚合 persisted canonical field

```31:32:backend/app/modules/attendance/reporting_service.py
    # canonical duration — duration_minutes IS NULL for open sessions
    total_work_minutes = sum(s.duration_minutes or 0 for s in sessions)
```

```76:77:backend/app/modules/attendance/reporting_service.py
    # canonical duration — duration_minutes IS NULL for open sessions
    total_work_minutes = sum(s.duration_minutes or 0 for s in sessions)
```

### 7.3 Forbidden patterns audit result

本次 inspected reporting code 中，未發現以下 forbidden pattern：

- 重新計算 `punch_out - punch_in` 當 canonical
- 將 break-adjusted 值寫回 canonical total
- 將 net minutes 當成 canonical total_work_minutes
- 將 canonical 與 derived 混在同一欄位中輸出
- 從 break punches / raw punches / alternative formulas 重算 canonical

### 7.4 Open session handling

針對 open session，`duration_minutes=None` 在 summary 中以 0 累加，不構成 canonical reinterpretation；這只是 aggregation 對未關閉 session 的輸出策略。

對應測試也存在：

```188:202:backend/app/modules/attendance/tests/test_reporting_user_summary.py
class TestUSR04NullDuration:
    def test_open_session_not_counted_in_work_minutes(self, client_a, db, user_a):
        now = datetime.now(timezone.utc)
        make_closed(db, COMPANY_A, user_a.id, now - timedelta(hours=20), duration_minutes=480)
        make_open(db, COMPANY_A, user_a.id, now - timedelta(hours=1))
        resp = get_user_summary(client_a, COMPANY_A, user_a.id)
        assert resp.status_code == 200
        d = resp.json()
        assert d["open_sessions"] >= 1
        assert d["closed_sessions"] >= 1
        # total_work_minutes must not include None duration
        assert d["total_work_minutes"] >= 480
```

**判定：Canonical Contract = PASS**

---

## 8. Response Shaping / Enrichment Findings

### 8.1 合理 presenter 範圍

目前 reporting 的 response shaping 主要包含：

- timezone conversion
- DTO / schema adaptation
- display_name enrichment
- user_id / company_id 補位

這些內容目前仍可被視為 API presenter 層，而非 business semantic ownership。

### 8.2 `display_name` enrichment

`sessions` endpoint 會先收集 user IDs，再做 `get_display_names` lookup，最後寫入 `SessionResponse.display_name`：

```108:123:backend/app/modules/attendance/api/reporting.py
    user_ids = list({str(s.user_id) for s in sessions})
    display_names = get_display_names(db, user_ids)

    items = []
    for s in sessions:
        items.append(SessionResponse(
            session_id=s.id,
            user_id=s.user_id,
            company_id=s.company_id,
            display_name=display_names.get(str(s.user_id)),
            punch_in_time=s.punch_in_time.astimezone(TZ_TAIPEI),
            punch_out_time=s.punch_out_time.astimezone(TZ_TAIPEI) if s.punch_out_time is not None else None,
            status=s.status,
            duration_minutes=s.duration_minutes,
            notes=s.notes,
        ))
```

這仍屬於 display enrichment，但也表示 reporting router 已非極薄層。

### 8.3 Actor-specific shaping

本次 inspected code 中，未見 actor-specific response schema 差異；actor 只影響資料 scope，不影響欄位語意。

### 8.4 Summary response normalization

user/company summary 皆會在 router 端做時間欄位 normalize：

```163:170:backend/app/modules/attendance/api/reporting.py
    summary = calculate_user_summary(sessions)

    summary["first_session_time"] = summary["first_session_time"].astimezone(TZ_TAIPEI) if summary["first_session_time"] is not None else None
    summary["last_session_time"] = summary["last_session_time"].astimezone(TZ_TAIPEI) if summary["last_session_time"] is not None else None

    return UserSummaryResponse(
        user_id=str(actor.user_id),
        **summary,
```

```212:219:backend/app/modules/attendance/api/reporting.py
    summary = calculate_company_summary(sessions)

    summary["first_session_time"] = summary["first_session_time"].astimezone(timezone.utc) if summary["first_session_time"] is not None else None
    summary["last_session_time"] = summary["last_session_time"].astimezone(timezone.utc) if summary["last_session_time"] is not None else None

    return CompanySummaryResponse(
        company_id=actor.active_company_id,
        **summary,
```

### 8.5 Judgment

- 目前仍屬合理 presenter / response layer
- 但 `sessions` endpoint enrichment + shaping 已偏重
- 若未來再增加欄位 remapping、export schema adaptation、更多 display decoration，router 成長風險會迅速提高

**判定：Response Shaping / Enrichment = Acceptable but Heavy**

---

## 9. Router / Mounting Coupling Findings

### 9.1 reporting router 自身邊界

`api/reporting.py` 自行定義 router：

```37:39:backend/app/modules/attendance/api/reporting.py
TZ_TAIPEI = ZoneInfo("Asia/Taipei")

router = APIRouter(prefix="/api/v1/attendance", tags=["attendance-v1"])
```

這代表 reporting route boundary 本身是清楚的。

### 9.2 與 `api.py` façade 的 inspected evidence

本次 inspected `backend/app/modules/attendance/api.py` 中，可見：

- legacy router import
- `router_v1` 宣告

但在本次已讀取範圍內，未看到 reporting router 的實際 merge / include 證據。

```50:56:backend/app/modules/attendance/api.py
from app.modules.attendance.api.legacy import router
from app.modules.attendance.api.helpers import _require_attendance_feature

logger = logging.getLogger(__name__)

# 新的 v1 router（主要業務邏輯）
router_v1 = APIRouter(prefix="/api/v1/attendance", tags=["attendance-v1"])
```

因此本票可下的結論是：

- reporting router 本身邊界清楚
- 與 `api.py` merge/mount 的最終耦合路徑，在本次 inspected evidence 中不足以做強判

### 9.3 Future mounting risk

雖然本次沒有直接看到 merge 問題，但從結構上可判讀：

- reporting 已採獨立 router 檔
- 這對邊界清晰有利
- 但若未來新的 reporting endpoints 不持續維持獨立邊界，而回流到大一統 façade，則 mount 層耦合風險會上升

**判定：Router / Mounting Coupling = Clear Router Boundary, Limited Mount Evidence**

---

## 10. Test Coverage

### 10.1 已覆蓋項目

#### A. sessions reporting

```1:12:backend/app/modules/attendance/tests/test_reporting_sessions.py
"""WP-11-06 Step 1: GET /api/v1/attendance/sessions Tests

SES-01 basic pagination
SES-02 start_date/end_date date filter
SES-03 Taipei midnight punch_in ownership
SES-04 cross-month session ownership
SES-05 status filter
SES-06 tenant isolation
SES-07 user scope
SES-08 open session NULL duration_minutes
SES-09 limit boundary validation
SES-10 total count matches actual count
"""
```

覆蓋內容包括：

- pagination
- date range
- Taipei business-date ownership
- cross-month ownership
- status filter
- tenant isolation
- employee user scope
- open session null duration
- limit validation
- total count consistency

#### B. user summary

```1:10:backend/app/modules/attendance/tests/test_reporting_user_summary.py
"""WP-11-06 Step 2: GET /api/v1/attendance/reports/user-summary Tests

USR-01  basic summary counts
USR-02  date range filter
USR-03  cross-midnight session counted in correct month
USR-04  NULL duration_minutes handling
USR-05  tenant isolation
USR-06  user scope enforcement
USR-07  naive datetime rejection (422)
USR-08  empty result returns zeros
"""
```

覆蓋內容包括：

- summary counts
- date range ownership
- cross-midnight ownership
- null duration handling
- tenant isolation
- own-scope summary
- aware / naive datetime boundary
- empty result behavior

#### C. company summary

```1:9:backend/app/modules/attendance/tests/test_reporting_company_summary.py
"""WP-11-06 Step 3: GET /api/v1/attendance/reports/company-summary Tests

CMP-01  basic company summary
CMP-02  date range filter
CMP-03  cross-midnight session ownership
CMP-04  NULL duration_minutes handling
CMP-05  tenant isolation
CMP-06  empty company dataset
CMP-07  naive datetime rejection (422)
"""
```

覆蓋內容包括：

- company summary counts
- unique users count expectation
- date range ownership
- null duration handling
- tenant isolation
- empty dataset
- naive datetime rejection

#### D. reporting helper boundary

```11:37:backend/app/modules/attendance/tests/test_reporting_helpers_boundary.py
class TestTaipeiBoundaryOwner:
    def test_get_taipei_today_uses_taipei_owner(self):
        now_utc = datetime(2026, 3, 11, 16, 30, 0, tzinfo=timezone.utc)
        assert get_taipei_today(now_utc) == date(2026, 3, 12)

    def test_business_date_builds_canonical_utc_range(self):
        boundary = build_taipei_business_date_boundary(date(2026, 3, 12))
        assert isinstance(boundary, TaipeiBusinessDateBoundary)
        assert boundary.business_date == date(2026, 3, 12)
        assert boundary.timezone_name == "Asia/Taipei"
```

覆蓋內容包括：

- Taipei date ownership
- canonical UTC range construction
- helper purity

### 10.2 未直接看到明確覆蓋的項目

本次 inspected tests 中，未直接看到以下責任的明確專測：

1. `reporting_service.py` 純 aggregation functions 的獨立 unit tests
2. `display_name` enrichment 的直接斷言
3. `company-summary` 的 admin gating 明確測試
4. feature gate disabled path 的 reporting-specific 測試
5. router / mount integration coupling 的專項測試

### 10.3 Coverage Judgment

目前測試對「現行 reporting contract」已具備中度以上支撐力，尤其在：

- scope
- tenant isolation
- business-date boundary
- null duration
- summary totals

但對未來 reporting 持續擴張的支撐度仍屬 **中等**，不是高強度可無限制擴張的 coverage 結構。

---

## 11. Future Growth Risk

**Medium**

### 原因

1. `reporting_service.py` 目前仍然乾淨，不是風險主體。
2. `reporting_repo.py` 目前責任也仍然乾淨，查詢邊界明確。
3. 主要風險集中於 `api/reporting.py`：
   - endpoint boundary
   - scope / permission gating
   - feature gate
   - query normalization
   - repo orchestration
   - enrichment
   - response shaping
   皆集中在同一檔案。
4. 若未來再加入：
   - 新 summary 類 endpoint
   - export 類 endpoint
   - 更複雜的 actor-specific output
   - 更多 display enrichment
   則最容易先失控的就是 `api/reporting.py`。
5. 目前還沒達到必拆門檻，但已接近「後續若持續新增功能，成長會開始不成比例集中」的區段。

---

## 12. Audit Conclusion

### 12.1 是否需要 P4 fix

**是，需要 P4 fix 關注。**

此處的判定是治理層面結論，不是修復方案。原因如下：

- canonical contract 目前仍正確
- reporting 仍是 consumer，不是 semantic owner
- 但 growth concentration 已經出現
- `api/reporting.py` 已開始成為變更熱點與責任聚集點

因此，本票結論不是「已有語意錯誤」，而是「已出現可觀察的 growth risk，值得在 P4 階段納入治理處理」。

### 12.2 是否可進 P5

**可進 P5，但必須帶 notes。**

理由：

- 目前 reporting 尚未違反 canonical contract
- 尚未出現 break-adjusted canonical mixing
- 尚未出現 reporting semantic ownership 漂移
- 尚未觀察到 reporting 承接 policy / close-flow 類 business rules

但同時：

- 不應假設目前 `api/reporting.py` 可無限制承載後續 reporting 擴張
- 若 P5 新增多個 reporting / export / summary 類能力，風險將快速升高

### 12.3 Final Judgment

- canonical / semantic contract：**PASS**
- reporting consumer-only contract：**PASS**
- growth / responsibility concentration：**PASS WITH NOTES**
- boundary cleanliness：**PASS WITH NOTES**
- overall result：**PASS WITH NOTES**

### 12.4 Final Statement

本次 P4_A1 審計結論為：

**reporting 尚未失守，但已出現明確的 growth concentration 訊號。**

目前仍可判定 reporting 保持在 consumer boundary 之內，且 canonical contract 未被破壞；然而 `api/reporting.py` 已開始承擔偏重的 orchestration 與 presenter 組合責任。若後續擴張沒有持續受治理控制，reporting growth 風險將由 Medium 進一步升高。
