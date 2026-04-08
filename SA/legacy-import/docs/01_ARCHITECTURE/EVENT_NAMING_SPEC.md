# Event Naming Specification

## 1. Purpose

This document defines the official naming rules for `EventBus` events used by the attendance system backend.

It exists to solve the following issues identified by P0-3D-2A Event Naming Convention Audit:

- the current production guard expects `demo.*` and `debug.*` namespaces
- an existing demo or testing event currently uses `test.event`
- `attendance.approved` is currently observed by both production handlers and demo subscribers
- `EventBus` event names, audit log actions, and persisted `event_type` strings all use dotted formats and can be confused without a formal boundary

This specification is part of the P0-3D hardening sequence:

- P0-3C introduced demo subscriber gating
- P0-3D-1 introduced production publish guard behavior for `demo.*` and `debug.*`
- P0-3D-2A audited the current repository state and concluded that the system needs a naming specification before any rename work is attempted

This document does not rename existing events. It provides the minimum governance needed so that future event additions and future migration tickets can be implemented consistently.

## 2. Scope

This specification applies only to `EventBus` event naming in backend code.

It governs:

- names passed to `EventBus.emit(...)`
- names passed to `EventBus.subscribe(...)`
- names documented or discussed as `EventBus` events in backend architecture decisions

It does not directly govern:

- audit log `action` strings
- database `event_type` fields used for persistence or reporting
- UI action names
- API route names
- log message wording

Those other dotted strings may resemble `EventBus` event names, but they belong to different naming spaces and must not be treated as equivalent unless an explicit design document says so.

## 3. Definitions

### 3.1 EventBus Event

A string identifier used as the routing key for in-process publish and subscribe behavior through `EventBus`.

### 3.2 Production Domain Event

An `EventBus` event that represents a real business-domain occurrence used by production application flow.

Example:

- `attendance.approved`

### 3.3 Demo Event

An `EventBus` event intended for demonstration-only flows, demo-only observability, or demo-only trigger paths.

A demo event must use the `demo.` namespace.

### 3.4 Debug Event

An `EventBus` event intended for debug-only observability, debug-only manual triggering, or debug-only internal inspection.

A debug event must use the `debug.` namespace.

### 3.5 Testing-only Name

A name used only for testing intent. Within `EventBus` naming, standalone `test.*` names are not an approved long-term namespace.

If an event is truly meant for debug-style manual testing of runtime behavior, it should use `debug.*`.

If an event is truly meant for demo behavior, it should use `demo.*`.

If a dotted string appears only in unit tests as data fixtures, mocks, or assertions and is not used by `EventBus.emit(...)` or `EventBus.subscribe(...)`, that string is outside this specification.

### 3.6 Audit / Event Type / Action String

A dotted string used by audit logging, persistence, analytics, or repository records rather than by `EventBus` publish-subscribe routing.

Examples include:

- audit log `action`
- persisted notification `event_type`
- reporting or filtering keys

These may look similar to `EventBus` events but are not automatically governed by the same rules.

## 4. Approved Naming Format

### 4.1 Current minimum standard

The approved minimum standard for `EventBus` event naming is:

- production business event: `domain.action`
- demo event: `demo.action`
- debug event: `debug.action`

### 4.2 Production format

Production events must use a business-domain namespace as the first segment.

Approved format:

- `domain.action`

Examples:

- `attendance.approved`
- `notifications.sent`
- `backup.completed`

### 4.3 Demo format

Demo events must use:

- `demo.action`

Examples:

- `demo.triggered`
- `demo.sample_published`

### 4.4 Debug format

Debug events must use:

- `debug.action`

Examples:

- `debug.triggered`
- `debug.inspect_requested`

### 4.5 Not allowed as approved long-term EventBus names

The following are disallowed as approved long-term `EventBus` names:

- `test.*`
- single-segment names such as `approved`
- generic names without domain such as `created` or `updated`
- names whose first segment does not clearly identify either a production domain or an approved environment namespace

### 4.6 Future extensibility

A future extension to `domain.entity.action` may be adopted if event volume or ambiguity increases.

That is not the current minimum requirement.

At the current system size, `domain.action` is the required baseline because it is simpler and already fits the existing production event pattern.

## 5. Allowed / Disallowed Examples

### 5.1 Allowed

- `attendance.approved`
  - production domain is clear
  - action is clear
- `demo.triggered`
  - demo namespace is explicit
- `debug.inspect_requested`
  - debug namespace is explicit
- `backup.completed`
  - business domain is clear

### 5.2 Disallowed

- `test.event`
  - unclear whether this means demo, debug, or generic testing
- `approved`
  - no domain boundary
- `created`
  - generic action with no domain boundary
- `event.created`
  - first segment is too generic to be a useful domain
- `demo.attendance.approved`
  - not approved under the current minimum standard because the spec currently standardizes on two segments only

### 5.3 Why these examples matter

The goal is not stylistic purity. The goal is to make each `EventBus` event name answer two questions immediately:

1. Is this a production domain event or an environment-scoped event?
2. Which domain or namespace owns it?

If the name cannot answer those questions, it should not be introduced as a new `EventBus` event.

## 6. Namespace Rules

### 6.1 Production events

Production events must use a production business-domain prefix.

The first segment must be the domain owner of the event, such as:

- `attendance`
- `notifications`
- `backup`

### 6.2 Demo and debug namespaces

`demo.*` and `debug.*` are reserved environment namespaces for non-production event naming.

Their role is to make environment-scoped behavior visible and governable.

### 6.3 `test.*` status

`test.*` is not an approved namespace for long-term `EventBus` event naming.

`test.*` may appear in legacy code or tests, but it should be treated as a migration candidate rather than a target pattern.

### 6.4 Segment count policy

Current standard:

- exactly two segments for newly introduced `EventBus` events

Possible future extension:

- `domain.entity.action`

That extension must be introduced by a separate design decision, not ad hoc within feature tickets.

### 6.5 Current minimum governance decision

For the current phase, the project standard is:

- production: `domain.action`
- demo: `demo.action`
- debug: `debug.action`
- disallow new `test.*` names

## 7. Domain Isolation Guidance

### 7.1 Naming and usage are different concerns

An event name defines naming identity. It does not fully define who is allowed to observe or process that event.

Naming rules and runtime usage patterns must be analyzed separately.

### 7.2 Production events observed by demo subscribers

A production event may be observed by a demo subscriber if a ticket explicitly allows that usage.

When this occurs, the event name remains a production event name.

This is a usage pattern, not a naming exception.

For example, if a demo subscriber observes `attendance.approved`, that does not convert the event into a demo event.

### 7.3 Demo naming must not replace production naming

A real production business event must not be renamed into a demo namespace merely because a demo flow consumes it.

If the event represents a real business occurrence, it should keep a production domain name.

### 7.4 Audit and persistence strings are separate namespaces

Audit `action`, persisted `event_type`, and similar dotted strings must not automatically be interpreted as `EventBus` event names.

Matching string shape does not imply matching semantic role.

If a future design intentionally maps between these layers, that mapping must be documented explicitly.

## 8. Migration Guidance (Non-breaking)

### 8.1 Existing `attendance.approved`

`attendance.approved` should be treated as a valid production domain event under this specification.

No rename is required by this document.

### 8.2 Existing `test.event`

`test.event` should be treated as a legacy or transitional name that does not meet the approved long-term standard.

This document does not rename it.

A future migration ticket may replace it with a more explicit `demo.*` or `debug.*` event name depending on actual intent.

### 8.3 How future rename work should be split

If rename work is needed, it should be split into separate, low-risk tickets:

1. classify the actual intent of each legacy non-compliant event
2. rename emit locations
3. rename subscribe locations
4. update debug or demo endpoints if needed
5. validate production isolation and test behavior

Rename work should not be bundled with unrelated refactors.

### 8.4 When registry / enum / constants become necessary

A registry, enum, or constants layer is not required at the current event count.

Such centralization should be considered only when at least one of the following becomes true:

- event count grows enough to create drift risk
- multiple modules begin reusing many shared event names
- typo risk becomes operationally significant
- cross-module governance can no longer be enforced by code review and a simple written specification

Until then, this document is the source of truth for naming rules.

## 9. Decision Summary

### 9.1 Must follow

- All new production `EventBus` events must use `domain.action`
- All new demo events must use `demo.action`
- All new debug events must use `debug.action`
- New `EventBus` names must clearly expose ownership through the first segment
- `EventBus` naming must be treated separately from audit actions and persisted event-type strings

### 9.2 Should avoid

- introducing `test.*` as a new long-term naming pattern
- introducing generic action-only names
- introducing domain-ambiguous first segments such as `event`
- treating demo subscriber observation as a reason to rename a production event into demo namespace

### 9.3 Not handled by this document

- direct code rename of existing events
- runtime enforcement beyond already existing implementation decisions
- registry or enum introduction
- audit log naming reform
- database schema changes

This specification is intentionally minimal. Its purpose is to align future naming decisions with the current architecture hardening work without forcing a broad refactor.
