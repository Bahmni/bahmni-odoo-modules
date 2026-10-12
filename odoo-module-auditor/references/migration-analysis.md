# Migration analysis principles

- Target is Odoo 20.0. Work through the four transition checklists in order and also apply all shared checks in `migration-rules/common.json`.
- For each potential issue, inspect the owning model/API and all related Python, XML, CSV, manifest, JavaScript, test, and dependency references.
- Verify against the exact target source and official documentation. Compare source and target implementations when the transition itself matters.
- Do not turn generic text matches into blanket replacements. In particular, investigate `virtual_available`, `uom.category`, `product_uom`, `product_uom_id`, `selection_add`/`ondelete`, `ir.rule`, `category_id`, stock view external IDs, controller response APIs, and frontend imports in their actual context.
- Preserve business semantics, data behavior, security boundaries, access restrictions, UOM conversion correctness, selection cleanup behavior, report output, and frontend UX.
- Separate confirmed incompatibilities from likely issues, false positives, and unresolved investigation leads.
- Propose minimal fixes and validation steps. Do not edit until the user explicitly approves.
- Database/runtime installation work is outside this skill; the user starts Odoo and inspects logs separately.
