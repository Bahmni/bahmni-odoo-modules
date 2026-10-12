# Source verification references

Prefer primary sources and the exact Odoo 20 branch/distribution being targeted:

- Odoo source repository, branch 20.0: https://github.com/odoo/odoo/tree/20.0
- Raw source files (use the source-cache helper): https://raw.githubusercontent.com/odoo/odoo/20.0/
- Odoo documentation: https://www.odoo.com/documentation/
- Odoo upgrade documentation: https://www.odoo.com/documentation/upgrade/

For each conclusion, record the precise URL, file path, symbol, and relevant lines/section. When practical, compare the source version and target version to establish whether a change occurred in the specific transition. Distinguish Community/Enterprise differences and deployment-specific addons. A URL or token match alone is not evidence of removal.

This source-only workflow does not use MCP, credentials, live instances, or database connections.


## Odoo 20 security migration evidence

- Odoo 20 developer documentation (primary source; verify exact deployed branch): https://www.odoo.com/documentation/20.0/developer/tutorials/restrict_data_access.html
- Odoo 20 source branch: https://github.com/odoo/odoo/tree/20.0
- Community migration analysis describing the `ir.model.access` + `ir.rule` to `ir.access` consolidation and CSV header/file change (secondary evidence; verify against the exact target source): https://github.com/OCA/maintainer-tools/issues/685

For the reported `KeyError: 'ir.model.access'`, check the CSV filename and manifest entry first, then inspect XML records with `model="ir.rule"`, access CSV headers, model IDs, group IDs, and security semantics. Do not just rename the file.
