# Audit workflow

1. Confirm repository root, addon path, current branch, and `git status --short`.
2. Read the skill's required references and all five files in `odoo-module-auditor/migration-rules/`.
3. Inspect `odoo-module-auditor/audit.sh` and `odoo-module-auditor/scripts/odoo-audit/scanner.py` to confirm read-only behavior.
4. Run `./odoo-module-auditor/audit.sh <module_path> --format=json` from repository root.
5. Capture stdout/stderr/exit status separately; parse stdout as JSON and verify `rule_catalog.loaded` is true with all five files listed.
6. Treat each regex match as an investigation lead. Check its owning model/file/context and verify against exact Odoo 20 source/docs through the local source cache.
7. Use the four transition checklists in order (16→17, 17→18, 18→19, 19→20), plus `common.json`. Do not assume checklist entries prove a version-specific change.
8. Classify each issue, record evidence, and propose a minimal file-by-file patch with risk and validation steps.
9. Stop and wait for explicit approval before edits.
10. After approval, re-check Git status, make only approved edits, inspect the scoped diff, run `git diff --check`, rerun the audit, and report remaining uncertainty.

No runtime/database step is part of this workflow. The user runs Odoo and checks logs separately.
