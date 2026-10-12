# JSON reporting contract

The scanner emits one JSON object on stdout. Important top-level fields include:

- `schema_version`, `module`, `module_path`, `source_version`, `target_version`
- `status`, `command`, `exit_code`, `output_format`, `parse_status`
- `rule_catalog`: loaded JSON filenames, common rule count, transition checklist counts, rule IDs, and load errors
- `summary`, `findings`, `tests_run`, `unresolved_risks`, `database_operations`

Each finding contains a stable rule ID, category, severity, file/line/column, evidence, heuristic message, proposed direction, classification, confidence, verification status, and approval status. Matches default to `needs_investigation`, low confidence, and unverified. They are not confirmed incompatibilities.

Exit code 0 means the scan ran successfully; it does not mean compatibility is proven. Exit 2 means usage/module path error. Exit 3 means a scanner error. The schema is a proposed contract; validate actual output before relying on a downstream consumer. No tests beyond those listed in `tests_run` should be claimed.
