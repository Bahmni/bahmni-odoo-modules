# Odoo 20 source cache workflow

Use the cache helper instead of repeating `curl` downloads into `/tmp`.

From the repository root:

```bash
python3 odoo-module-auditor/scripts/odoo-audit/source_cache.py "https://raw.githubusercontent.com/odoo/odoo/20.0/odoo/addons/base/models/ir_actions.py"
```

The command prints the local path. Use it for read-only inspection, for example:

```bash
CACHED="$(python3 odoo-module-auditor/scripts/odoo-audit/source_cache.py "https://raw.githubusercontent.com/odoo/odoo/20.0/odoo/addons/base/models/ir_actions.py")"
grep -nE "view_mode|'tree'|\"tree\"|'list'" "$CACHED" | head -40
```

- Cache root: `odoo-module-auditor/cache/20.0/`, inside the single auditor folder.
- Files younger than seven days are reused; missing or stale files are downloaded. Use `--refresh` to force a fetch.
- Only HTTPS `raw.githubusercontent.com` URLs with an explicit `20.0` branch segment are accepted.
- A `.metadata.json` sidecar records requested/final URL, branch, fetch time, and byte count.
- Cache content is ignored by `odoo-module-auditor/.gitignore` and should not be committed.
- The branch can move. Record the source commit/revision when practical, and inspect surrounding code. A grep match alone does not establish incompatibility.
- The helper does not edit the addon, run Odoo, invoke Docker, connect to a database, or access a live instance.
- Do not fall back silently to downloads in `/tmp` or a different cache directory if this helper fails; report the issue and ask before changing approach.
