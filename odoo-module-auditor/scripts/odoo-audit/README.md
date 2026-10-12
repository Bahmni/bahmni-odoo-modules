# Audit and source-cache scripts

## Scanner

Run from the repository root:

```bash
./odoo-module-auditor/audit.sh path/to/addon --format=json
```

The scanner reads source/config text files from the specified addon and emits JSON to stdout. It is heuristic and read-only: it does not edit files, run Odoo, connect to a database, invoke Docker, or perform database operations. Exit 0 means scanning completed, not that compatibility is proven.

The scanner loads and validates the five separate JSON rule files in `odoo-module-auditor/migration-rules/` and includes load status/counts in `rule_catalog`. The regex scanner remains a quick pattern pass; the skill must separately read and apply the richer rule guidance and transition checklists.

## Source cache

`source_cache.py` accepts an HTTPS raw GitHub URL on the explicit `20.0` branch and prints the cached local file path. Default cache is `odoo-module-auditor/cache/20.0/`, under the auditor directory. Fresh files are reused for seven days; `--refresh` forces a download. Only the cache helper writes files, and only inside the auditor cache directory. It never writes into the addon.
