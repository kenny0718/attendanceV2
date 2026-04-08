# WP-11-08 Leave Request System

Status: DESIGN

---

# Goal

Implement employee leave request system.

Employees can:

- create leave request
- view their leave history

Managers can:

- approve / reject leave requests

---

# Leave Types

Initial types:

- sick_leave
- annual_leave
- personal_leave
- unpaid_leave

Leave types are configurable.

---

# Core Flow

Employee

create request
→ manager review
→ approved / rejected

---

# Data Model

Table: leave_requests

fields

id
company_id
user_id
leave_type
start_date
end_date
reason
status
created_at
updated_at

status values

pending
approved
rejected

---

# API

POST /api/v1/leave/request

GET /api/v1/leave/my-requests

POST /api/v1/leave/{id}/approve

POST /api/v1/leave/{id}/reject

---

# UI

User page

My Leave Requests

Admin page

Leave Approval