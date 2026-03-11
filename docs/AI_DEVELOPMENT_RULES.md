Goal

Create a permanent development rule document to prevent file overwrite, backup chaos, and accidental source corruption when using AI tools (Cursor) to modify the project.

Create file:

docs/AI_DEVELOPMENT_RULES.md

Content requirements:

1. Source File Protection Rules

Never rewrite entire source files unless explicitly instructed.

Allowed behavior:

* modify specific code blocks
* patch sections
* add or update functions

Forbidden behavior:

* overwrite entire files
* generate temporary files then copy over source
* restore old backup files automatically

2. Backup Policy

Backups must NOT be placed inside `src/` directories.

Allowed backup format:

.backup_YYYYMMDD_HHMMSS

Example:

Home.vue.backup_20260310_2100

Recommended location:

/backups/frontend/

Rules:

* only keep latest 2 backups
* delete older backups regularly

3. Temporary File Rules

Never use `/tmp/*.vue` or `/tmp/*.js` to overwrite project source files.

Temporary analysis files may exist in `/tmp`, but must never be copied into `src`.

4. Empty File Protection

Before writing any source file, verify the file is not empty or corrupted.

If a read returns empty content:

* stop modification
* report error
* do NOT overwrite

5. File Rewrite Safety

If modification affects more than 30% of a file:

* create timestamp backup
* apply minimal patch instead of rewrite

6. Project Stability Policy

When project state is marked "stable":

* avoid structural refactors
* avoid mass file rewrites
* modify only targeted sections

7. Snapshot Requirement

Before large refactors:

* Home.vue restructuring
* store logic changes
* router changes

Create LXC snapshot first.

Purpose

Prevent situations where:

* source files become empty
* fixes disappear
* backups overwrite correct versions
