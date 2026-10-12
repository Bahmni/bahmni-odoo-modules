# Migration rules

`common.json` contains shared rules and mandatory checks transcribed from the user’s manual Odoo 16→20 migration notes. Rules with a `scanner` object are executed by `scripts/odoo-audit/scanner.py`; rules without one remain mandatory manual review checks.

Each transition file contains mandatory rule references for the corresponding step in the 16→20 path. Do not skip a rule because the scanner did not match a token. For each rule, record applicability and exact source evidence. User-reported claims must be verified against the target branch and distribution before being called confirmed.

Security note: Odoo 20 migration evidence indicates `ir.model.access` and `ir.rule` are combined into `ir.access`; verify the target CSV filename/header (expected `security/ir.access.csv` in the referenced migration evidence) and preserve the effective access semantics. Do not merely rename files or delete record rules.
