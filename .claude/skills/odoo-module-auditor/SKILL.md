---
name: odoo-module-auditor
description: Audits custom Odoo addons for migration from Odoo 16.0 to Odoo 20.0 using the self-contained repository folder odoo-module-auditor. Reads its five JSON migration rule files and persistent Odoo 20 source cache, emits machine-readable JSON, proposes minimal fixes, and waits for explicit approval before editing.
---

# Odoo Module Auditor — Odoo 16 → Odoo 20

## Repository layout contract

This skill is deliberately split into exactly two repository-root locations:

- `.claude/skills/odoo-module-auditor/SKILL.md` — the Claude Code skill entry point only.
- `odoo-module-auditor/` — all auditor implementation files, five migration-rule JSON files, supporting references, schema, and the local source-cache directory.

**Do not create other auditor directories or copy scripts/rules into the repository root.** Do not put source cache files in `/tmp`, `~/.cache`, or the custom addon. The cache defaults to `odoo-module-auditor/cache/20.0/` and is excluded from Git by the folder's `.gitignore`.

All paths below are relative to the repository root unless stated otherwise.

## Purpose and safety defaults

Migrate custom Odoo 16.0 addons to Odoo 20.0. Use the flow: **inspect → baseline scan → read all migration rules → verify findings against exact Odoo 20 sources → propose a minimal file-by-file patch → wait for explicit approval → apply only approved edits → re-audit → report**.

- Odoo 20.0 is the only target. Analyze intermediate transitions 16→17, 17→18, 18→19, and 19→20 using the corresponding JSON files.
- If the addon path is unclear, ask the user. Do not assume the repository root itself is the addon.
- Audit and source research may run autonomously when side effects are understood.
- Never edit source, manifest, XML, CSV, JS, tests, or configuration files until the user explicitly approves the proposed changes.
- Database operations are outside this skill's scope. Do not connect to a live Odoo instance, use database credentials, invoke database tools, reset/drop/recreate/migrate databases, or run Odoo/Docker. The user starts Odoo and checks runtime logs separately.
- Do not use MCP or request/store credentials for this workflow.
- Preserve unrelated changes; never stage or commit automatically.

## Required files — read from `odoo-module-auditor/` only

Before making migration recommendations, inspect and read:

- `odoo-module-auditor/README.md`
- `odoo-module-auditor/migration-rules/common.json`
- `odoo-module-auditor/migration-rules/16-to-17.json`
- `odoo-module-auditor/migration-rules/17-to-18.json`
- `odoo-module-auditor/migration-rules/18-to-19.json`
- `odoo-module-auditor/migration-rules/19-to-20.json`
- `odoo-module-auditor/references/workflow.md`
- `odoo-module-auditor/references/approval-and-safety.md`
- `odoo-module-auditor/references/migration-analysis.md`
- `odoo-module-auditor/references/reporting-contract.md`
- `odoo-module-auditor/references/source-references.md`
- `odoo-module-auditor/references/source-cache.md`
- `odoo-module-auditor/schemas/migration-audit.schema.json`

The common JSON contains shared rules plus mandatory audit checks transcribed from all manually identified migration notes, including XML `attrs`/`states`, security CSV/model changes, stock/UOM changes, ORM/API changes, manifests, accounting, mail and frontend migrations. The four transition JSON files now include concrete rule references and mandatory transition checks. The scanner executes `scanner.pattern` entries from `common.json`; still inspect the full rule descriptions even when no token matches. Every note must be marked applicable, not applicable, false positive, or needs investigation with source evidence. The presence of a note is not proof that the claim is true for every model/edition; verify exact source/docs before proposing a fix. Do not skip any rule file.

## Baseline audit

1. Confirm repository root, addon path, branch, and `git status --short`.
2. Inspect `odoo-module-auditor/audit.sh` and `odoo-module-auditor/scripts/odoo-audit/scanner.py` before running if they are modified.
3. Run from repository root:
   `./odoo-module-auditor/audit.sh <module_path> --format=json`
4. Capture stdout, stderr, and exit code separately; parse stdout with a JSON parser.
5. Exit code 0 means the heuristic scan completed, not that the addon is compatible. Exit 2 indicates usage/path error; exit 3 indicates scanner error.
6. Check the output's `rule_catalog` object. It must report all five JSON rule files loaded. If not, report the missing/invalid rule files and do not silently proceed as if all rules were read.
7. All scanner matches are investigation leads. The scanner must not label a match a confirmed incompatibility without independent verification. A legacy `security/ir.model.access.csv` filename is emitted as a security-critical finding; verify conversion to the Odoo 20 `ir.access` model/file format and preserve old ACL plus record-rule semantics.

## Source investigation and persistent cache

Use `odoo-module-auditor/scripts/odoo-audit/source_cache.py` for official Odoo source files rather than repeatedly downloading to `/tmp`.

Example, from repository root:

`python3 odoo-module-auditor/scripts/odoo-audit/source_cache.py "https://raw.githubusercontent.com/odoo/odoo/20.0/odoo/addons/base/models/ir_actions.py"`

The command prints the cached file path. Use the printed path with `grep`, `sed`, or other read-only inspection. The cache is stored under `odoo-module-auditor/cache/20.0/`, inside the single auditor directory. Fresh entries (up to seven days by default) are reused; missing/stale files are downloaded. `--refresh` forces a download. Only HTTPS `raw.githubusercontent.com` URLs with an explicit `20.0` branch path are accepted. Metadata is stored beside each cached source file. Since branch `20.0` moves, record source URLs and commit/revision when practical. Never treat a text match as proof; inspect surrounding implementation and compare source versions where relevant.

If network access or the helper fails, report the failure and ask before using another download method. Do not silently fall back to repeated direct `curl` downloads or store sources elsewhere.

## Verify and propose fixes

For every relevant finding:

1. Trace it to the exact addon file, line, model, field, view, external ID, controller, asset, or dependency.
2. Read the applicable common rule and all relevant transition checklists.
3. Verify the actual Odoo 20 behavior against official documentation and the exact Odoo 20 source/distribution. For version-transition claims, compare source versions where practical.
4. Classify as `confirmed_incompatibility`, `likely_issue`, `false_positive`, or `needs_investigation`; include source URL/path, relevant symbol/line, and reasoning.
5. Preserve business logic, access restrictions, record-rule semantics, UOM conversions, selection lifecycle behavior, report behavior, and frontend UX.
6. Provide a minimal patch proposal, impacted files, tests/checks, and risks. **Stop and wait for explicit approval before editing.**
7. After approval, re-check Git status, change only approved files, run `git diff --check`, inspect the scoped diff, and rerun the JSON audit.

Do not automatically rewrite all occurrences of a token. In particular, do not assume `virtual_available`, `uom.category`, `product_uom`, `product_uom_id`, `ir.rule`, `category_id`, or Font Awesome references are invalid merely because they match a scanner pattern.

## Completion report

Report addon, source/target versions, command, JSON parse status, exit code, rule catalog load status, findings by severity/classification, verified references, proposed/applied changes and approval status, re-audit comparison, checks actually run, unresolved risks, and database operations (always `none` for this skill).

## Cleanup after migration

When the user confirms the migration workflow is finished, the auditor can be removed by deleting only these two repository-root locations:

- `.claude/skills/odoo-module-auditor/`
- `odoo-module-auditor/`

Do not delete or alter unrelated `.claude` content. If `odoo-module-auditor/` is tracked, review the scoped Git diff before removal/commit.
