# Odoo Module Auditor — Odoo 16 → Odoo 20

A self-contained, read-only audit toolkit for custom Odoo addons. This folder is the only auditor implementation directory to add to your repository. The Claude Code entry point lives separately at `.claude/skills/odoo-module-auditor/SKILL.md`.

## Layout

```text
repository-root/
├── .claude/
│   └── skills/odoo-module-auditor/SKILL.md
└── odoo-module-auditor/
    ├── audit.sh
    ├── README.md
    ├── .gitignore
    ├── cache/                 # local Odoo 20 source cache, populated on demand
    ├── migration-rules/
    │   ├── common.json
    │   ├── 16-to-17.json
    │   ├── 17-to-18.json
    │   ├── 18-to-19.json
    │   ├── 19-to-20.json
    │   └── README.md
    ├── references/            # workflow and safety guidance
    ├── schemas/migration-audit.schema.json
    └── scripts/odoo-audit/
        ├── scanner.py
        └── source_cache.py
```

No other auditor directories are required. Do not unpack the ZIP directly over existing `.claude` content without reviewing it first.

## Run a JSON audit

From repository root:

```bash
chmod +x odoo-module-auditor/audit.sh
./odoo-module-auditor/audit.sh path/to/your_addon --format=json
```

Validate the output:

```bash
./odoo-module-auditor/audit.sh path/to/your_addon --format=json | python3 -m json.tool
```

Exit codes: `0` means the scan ran; it does **not** mean the addon is compatible. `2` indicates a usage or module path error. `3` indicates a scanner error. JSON output includes `rule_catalog`, which lists the rule files loaded and their counts. Confirm `loaded: true` and all five files before relying on the report.

## Five migration rule files

- `migration-rules/common.json`: shared cross-version rules, including security/ACLs, record rules, manifest dependencies and file paths, XML views, stock references, ORM/controller APIs, UOMs, `selection_add` lifecycle behavior, decimal precision, HTML/pickle APIs, frontend JavaScript, and test/validation guidance.
- `migration-rules/16-to-17.json`
- `migration-rules/17-to-18.json`
- `migration-rules/18-to-19.json`
- `migration-rules/19-to-20.json`

The four transition files contain concrete mandatory rule references plus required verification checklists. `common.json` includes 86 shared rules, including 44 mandatory checks transcribed from all user-provided manual migration notes. The scanner executes each common rule with a `scanner.pattern` and separately flags the legacy `security/ir.model.access.csv` path. Every check must be reviewed and classified; a match is a required investigation lead, not proof of incompatibility. Verify against exact Odoo 20 source/documentation and deployment edition. The notes conflict on the Odoo 20 security filename: do not preserve `ir.model.access.csv` blindly; verify the target `ir.access` format and preserve effective permissions/record domains.

## Persistent source cache

The helper `scripts/odoo-audit/source_cache.py` caches official Odoo source files under `odoo-module-auditor/cache/20.0/`. It does not create a separate cache directory at the repository root, in `/tmp`, or under the user's home directory. Files are reused for seven days by default; stale/missing files are fetched from `raw.githubusercontent.com` on the explicit Odoo `20.0` branch. `--refresh` forces a fresh download. Source and metadata files in `cache/` are ignored by this folder's `.gitignore`.

Example:

```bash
python3 odoo-module-auditor/scripts/odoo-audit/source_cache.py \
  "https://raw.githubusercontent.com/odoo/odoo/20.0/odoo/addons/base/models/ir_actions.py"
```

Use the returned path for subsequent `grep`/`sed` inspection. Review context, not just matching lines. The moving branch should not be treated as immutable; record commit/revision information when practical.

## Safety boundaries

- Read-only scanner; no edits to addon source.
- No Odoo server execution, Docker invocation, live instance connection, database connection, or database operation.
- No MCP configuration or credentials required.
- The skill must request explicit approval before editing any source files.
- No automatic Git staging or commits.
- The user starts Odoo and checks runtime logs separately.

## Remove after migration

Once finished, remove only `.claude/skills/odoo-module-auditor/` and `odoo-module-auditor/`. Review Git status first and preserve unrelated `.claude` files or existing settings.
