#!/usr/bin/env python3
"""Read-only Odoo 16 -> 20 source-pattern scanner.

All findings are heuristics requiring verification against Odoo 20 source/docs.
The scanner never edits files, executes Odoo, connects to a database, or runs Docker.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Pattern

SOURCE_VERSION = "16.0"
TARGET_VERSION = "20.0"
SCHEMA_VERSION = "1.0"

EXCLUDED_DIRS = {
    ".git", ".hg", ".svn", "__pycache__", ".venv", "venv",
    "node_modules", ".mypy_cache", ".pytest_cache", "dist", "build", "cache"
}

# Each pattern is a lead for investigation, NOT a confirmed incompatibility.
# Avoid wording that declares a pattern removed unless independently verified.
RULES = [
    {
        "id": "ODOO-MIG-SEC-001", "category": "security",
        "severity": "warning", "transition": "needs_verification",
        "pattern": r"\bperm_(?:read|write|create|unlink)\b",
        "globs": ["security/**/*.csv", "security/**/*.xml", "security/**/*.yml", "security/**/*.yaml"],
        "message": "Access-control permission token found. Verify the CSV/XML structure and access semantics against Odoo 20; the token alone does not prove incompatibility.",
        "suggested_fix": "Inspect the exact security file and Odoo 20 access-control implementation. Do not rename files or change permissions based on this match alone."
    },
    {
        "id": "ODOO-MIG-SEC-002", "category": "security",
        "severity": "warning", "transition": "needs_verification",
        "pattern": r"\bir\.rule\b",
        "globs": ["security/**/*", "**/*.xml", "**/*.csv"],
        "message": "Reference to ir.rule found. Record rules are a normal Odoo security concept in many versions; verify the specific reference against the target source rather than assuming the model was removed.",
        "suggested_fix": "Check the referenced external ID/model and Odoo 20 source. Preserve record-level restrictions and never broaden access without explicit review."
    },
    {
        "id": "ODOO-MIG-SEC-003", "category": "security",
        "severity": "warning", "transition": "needs_verification",
        "pattern": r"\bcategory_id\b",
        "globs": ["security/**/*.xml", "**/*.xml", "**/*.py"],
        "message": "category_id token found. Determine which model/field it refers to; a text match is not sufficient to establish that res.groups.category_id is incompatible.",
        "suggested_fix": "Inspect the surrounding XML/Python and verify the field on the actual target model."
    },
    {
        "id": "ODOO-MIG-MANIFEST-001", "category": "manifest_dependencies",
        "severity": "warning", "transition": "needs_verification",
        "pattern": r"""['"]qweb['"]\s*:""",
        "globs": ["__manifest__.py"],
        "message": "Legacy-looking qweb manifest key found. Verify the target version's manifest and asset loading requirements.",
        "suggested_fix": "Check Odoo 20 manifest/asset documentation and preserve template load order before changing declarations."
    },
    {
        "id": "ODOO-MIG-MANIFEST-002", "category": "manifest_dependencies",
        "severity": "warning", "transition": "needs_verification",
        "pattern": r"\bindustry_fsl\b",
        "globs": ["__manifest__.py"],
        "message": "Dependency token industry_fsl found. Verify whether the dependency exists and what module replaces it in the exact Odoo 20 distribution being targeted.",
        "suggested_fix": "Inspect the target addons source and dependent features before changing the dependency."
    },
    {
        "id": "ODOO-MIG-MANIFEST-003", "category": "manifest_dependencies",
        "severity": "warning", "transition": "needs_verification",
        "pattern": r"""['"]([^'"]+\.(?:xml|csv|js|css|scss|py|po|json))['"]""",
        "globs": ["__manifest__.py"],
        "message": "Potential manifest-declared file path found. Check existence relative to the module root; this scanner only recognizes simple quoted paths.",
        "suggested_fix": "Verify the path exists and is included in the correct manifest section. Dynamic Python expressions and nested structures may require manual review.",
        "special": "manifest_paths"
    },
    {
        "id": "ODOO-MIG-VIEW-001", "category": "xml_view",
        "severity": "warning", "transition": "needs_verification",
        "pattern": r"<\s*tree(?:\s|>)",
        "globs": ["views/**/*.xml", "**/*.xml"],
        "message": "XML tree element found. Check whether this is an Odoo list-view declaration that requires migration for the target version; avoid changing unrelated XML tags or embedded text.",
        "suggested_fix": "Verify view type and parent view against Odoo 20, then update related references consistently if required."
    },
    {
        "id": "ODOO-MIG-VIEW-002", "category": "xml_view",
        "severity": "warning", "transition": "needs_verification",
        "pattern": r"\battrs\s*=",
        "globs": ["views/**/*.xml", "**/*.xml"],
        "message": "Legacy attrs attribute found. Verify target-version view syntax and translate the original condition without changing its logic.",
        "suggested_fix": "Translate each condition to supported expressions only after preserving boolean grouping, operators, and field references."
    },
    {
        "id": "ODOO-MIG-VIEW-003", "category": "xml_view",
        "severity": "warning", "transition": "needs_verification",
        "pattern": r"\bstates\s*=",
        "globs": ["views/**/*.xml", "**/*.xml"],
        "message": "states attribute found. Verify the specific view/action context and target-version behavior.",
        "suggested_fix": "Translate the original state logic only after checking the target-version view rules."
    },
    {
        "id": "ODOO-MIG-VIEW-004", "category": "assets_templates",
        "severity": "info", "transition": "needs_verification",
        "pattern": r"\bfa\s+fa-[A-Za-z0-9_-]+|icon\s*=\s*['\"]fa-",
        "globs": ["views/**/*.xml", "**/*.xml", "static/**/*"],
        "message": "Font Awesome-style class/icon found. This is a visual compatibility lead, not proof that the icon is unsupported.",
        "suggested_fix": "Check the target web-client assets and supported icon set before replacing the icon."
    },
    {
        "id": "ODOO-MIG-VIEW-005", "category": "xml_view",
        "severity": "warning", "transition": "needs_verification",
        "pattern": r"\btarget\s*=\s*['\"]inline['\"]",
        "globs": ["**/*.xml", "**/*.py"],
        "message": "Action target inline found. Verify target-version action semantics before replacing it.",
        "suggested_fix": "Determine intended navigation behavior and use a supported target only if behavior is preserved."
    },
    {
        "id": "ODOO-MIG-VIEW-006", "category": "xml_view",
        "severity": "warning", "transition": "needs_verification",
        "pattern": r"\breport_file\b",
        "globs": ["views/**/*.xml", "reports/**/*.xml", "**/*.py", "**/*.xml"],
        "message": "report_file reference found. Verify the exact field/model and report definition against Odoo 20.",
        "suggested_fix": "Inspect the report action and target model before changing report fields."
    },
    {
        "id": "ODOO-MIG-STOCK-000", "category": "python_orm",
        "severity": "info", "transition": "needs_verification",
        "pattern": r"\bvirtual_available\b",
        "globs": ["**/*.py", "**/*.xml", "**/*.js"],
        "message": "virtual_available reference found. Do not assume it was removed: verify the owning model, context, and exact Odoo 20 implementation.",
        "suggested_fix": "Trace the field through the owning model and all callers, then verify it against the Odoo 20 source. Keep it if supported; do not replace it based on the token alone."
    },
    {
        "id": "ODOO-MIG-STOCK-001", "category": "python_orm",
        "severity": "warning", "transition": "needs_verification",
        "pattern": r"\bmove_ids_without_package\b",
        "globs": ["**/*.xml", "**/*.py"],
        "message": "move_ids_without_package reference found. Verify the field and intended view/model against the Odoo 20 source.",
        "suggested_fix": "Check the exact parent model/view and all call sites before changing the field reference."
    },
    {
        "id": "ODOO-MIG-STOCK-002", "category": "xml_view",
        "severity": "warning", "transition": "needs_verification",
        "pattern": r"\bstock\.view_stock_move_line_operation_list\b",
        "globs": ["**/*.xml", "**/*.py"],
        "message": "Legacy-looking stock view external ID found. Verify that the ID exists in the target Odoo 20 source.",
        "suggested_fix": "Search the exact Odoo 20 addons source for the external ID and update inheritance only after identifying the correct replacement."
    },
    {
        "id": "ODOO-MIG-ORM-001", "category": "python_orm",
        "severity": "warning", "transition": "needs_verification",
        "pattern": r"\bodoo\.osv\b",
        "globs": ["**/*.py"],
        "message": "odoo.osv reference found. Verify the imported symbol and its availability; this match does not prove the entire package is removed.",
        "suggested_fix": "Check target source for the exact imported API and use an equivalent only if behavior is preserved."
    },
    {
        "id": "ODOO-MIG-CONTROLLER-001", "category": "controllers_api",
        "severity": "warning", "transition": "needs_verification",
        "pattern": r"\bcontent_disposition\b",
        "globs": ["**/*.py"],
        "message": "content_disposition reference found. Determine the import path and usage; the symbol name alone does not prove an incompatible import.",
        "suggested_fix": "Verify the exact import and target-version API before changing response headers or download behavior."
    },
    {
        "id": "ODOO-MIG-ORM-002", "category": "python_orm",
        "severity": "warning", "transition": "needs_verification",
        "pattern": r"\bproduct_uom_id\b",
        "globs": ["models/**/*.py", "**/*.py"],
        "message": "product_uom_id reference found. Verify the model on which it is used; field names can differ between models.",
        "suggested_fix": "Resolve the model and field definition in Odoo 20 before editing."
    },
    {
        "id": "ODOO-MIG-TRACKING-001", "category": "python_orm",
        "severity": "info", "transition": "needs_verification",
        "pattern": r"\bmail\.tracking\.value\b",
        "globs": ["**/*.py", "**/*.xml", "**/*.csv"],
        "message": "mail.tracking.value reference found. Verify target-version persistence and access behavior before relying on historical tracking rows.",
        "suggested_fix": "Check the target model definition and business requirements for tracking history."
    },
    {
        "id": "ODOO-MIG-ACCOUNT-001", "category": "python_orm",
        "severity": "warning", "transition": "needs_verification",
        "pattern": r"\baccount\.group\b",
        "globs": ["**/*.py", "**/*.xml", "**/*.csv"],
        "message": "account.group reference found. Verify whether the model/external ID remains available in the target edition and installed addons.",
        "suggested_fix": "Inspect target account modules and dependent behavior; do not replace with a hierarchy assumption without source evidence."
    },
    {
        "id": "ODOO-MIG-HR-001", "category": "python_orm",
        "severity": "warning", "transition": "needs_verification",
        "pattern": r"\bhr\.work\.entry\b",
        "globs": ["**/*.py", "**/*.xml", "**/*.csv"],
        "message": "hr.work.entry reference found. Verify target-version model availability and dependency requirements.",
        "suggested_fix": "Check Odoo 20 source and installed modules before changing model references."
    },
    {
        "id": "ODOO-MIG-UOM-001", "category": "python_orm",
        "severity": "warning", "transition": "needs_verification",
        "pattern": r"\buom\.category\b",
        "globs": ["**/*.py", "**/*.xml", "**/*.csv"],
        "message": "uom.category reference found. Verify target-version model and field availability; do not assume the model was removed from a text match.",
        "suggested_fix": "Inspect Odoo 20 UoM models, dependencies, and all related domains/fields."
    },
    {
        "id": "ODOO-MIG-UOM-002", "category": "python_orm",
        "severity": "info", "transition": "needs_verification",
        "pattern": r"\bproduct_uom\b",
        "globs": ["models/**/*.py", "**/*.py"],
        "message": "product_uom token found. The correct field may depend on the model and version; this match may include legitimate identifiers.",
        "suggested_fix": "Inspect model definitions, compute dependencies, domains, and related views before proposing a rename."
    },
    {
        "id": "ODOO-MIG-ORM-003", "category": "python_orm",
        "severity": "warning", "transition": "needs_verification",
        "pattern": r"\bselection_add\s*=",
        "globs": ["**/*.py"],
        "message": "selection_add found. Check the corresponding field definition and whether the target version requires an ondelete policy for that extension.",
        "suggested_fix": "Inspect the complete field declaration and choose a lifecycle-appropriate policy only if required."
    },
    {
        "id": "ODOO-MIG-IMPORT-001", "category": "python_orm",
        "severity": "warning", "transition": "needs_verification",
        "pattern": r"\bdecimal_precision\b",
        "globs": ["**/*.py"],
        "message": "decimal_precision reference found. Verify whether it is an import, a module dependency, or an unrelated identifier.",
        "suggested_fix": "Check target source and migrate precision handling while preserving numeric behavior."
    },
    {
        "id": "ODOO-MIG-IMPORT-002", "category": "python_orm",
        "severity": "warning", "transition": "needs_verification",
        "pattern": r"\bhtml_keep_url\b",
        "globs": ["**/*.py"],
        "message": "html_keep_url reference found. Verify exact import and availability in Odoo 20.",
        "suggested_fix": "Inspect the target utility implementation and preserve HTML sanitization/link behavior."
    },
    {
        "id": "ODOO-MIG-IMPORT-003", "category": "python_orm",
        "severity": "warning", "transition": "needs_verification",
        "pattern": r"from\s+odoo\.tools\s+import\s+.*\bpickle\b",
        "globs": ["**/*.py"],
        "message": "Possible pickle import from odoo.tools found. Confirm the import statement and target API.",
        "suggested_fix": "If the import is invalid, use the appropriate standard-library API only after reviewing serialization and security implications."
    },
    {
        "id": "ODOO-MIG-CONTROLLER-002", "category": "controllers_api",
        "severity": "warning", "transition": "needs_verification",
        "pattern": r"\btype\s*=\s*['\"]json['\"]",
        "globs": ["controllers/**/*.py", "**/*.py"],
        "message": "Route type json found. Verify the route type supported by the exact Odoo 20 controller API and whether this is an actual route declaration.",
        "suggested_fix": "Check the decorator and target controller API; preserve request/response protocol and authentication semantics."
    },
    {
        "id": "ODOO-MIG-JS-001", "category": "javascript_owl",
        "severity": "warning", "transition": "needs_verification",
        "pattern": r"\bweb\.(?:framework|session)\b",
        "globs": ["static/**/*.js", "static/**/*.xml"],
        "message": "Legacy-looking web.framework/web.session reference found. Verify module availability and replacement in the target web client.",
        "suggested_fix": "Inspect imports, registries, services and call sites against Odoo 20 frontend source."
    },
    {
        "id": "ODOO-MIG-JS-002", "category": "javascript_owl",
        "severity": "warning", "transition": "needs_verification",
        "pattern": r"\bsession\.get_file\b",
        "globs": ["static/**/*.js"],
        "message": "session.get_file reference found. Verify target web-client API and download semantics.",
        "suggested_fix": "Use the supported target-version download API only after checking parameters, authentication, and error handling."
    },
    {
        "id": "ODOO-MIG-JS-003", "category": "javascript_owl",
        "severity": "warning", "transition": "needs_verification",
        "pattern": r"\bframework\.blockUI\b|\bframework\.unblockUI\b",
        "globs": ["static/**/*.js"],
        "message": "Legacy blockUI/unblockUI reference found. Verify target-version UI service APIs and lifecycle semantics.",
        "suggested_fix": "Check Odoo 20 service APIs and ensure blocking is always paired with cleanup on success and failure."
    }
]


def load_json_scanner_rules() -> list[dict]:
    """Load mandatory scanner patterns from common.json so the JSON rules are executable."""
    rules_path = Path(__file__).resolve().parents[2] / "migration-rules" / "common.json"
    try:
        catalog = json.loads(rules_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    loaded = []
    for rule in catalog.get("rules", []):
        spec = rule.get("scanner")
        if not isinstance(spec, dict) or not spec.get("pattern"):
            continue
        loaded.append({
            "id": rule["rule_id"],
            "category": rule.get("category", "migration"),
            "severity": rule.get("severity", "warning"),
            "transition": "mandatory_note_check",
            "pattern": spec["pattern"],
            "globs": spec.get("globs", ["**/*"]),
            "message": rule.get("title", "Mandatory migration note pattern found") + ". This is a required investigation lead from the manual migration notes; verify exact Odoo 20 source before classifying it as incompatible.",
            "suggested_fix": rule.get("remediation_guidance", "Verify target source and propose a behavior-preserving fix only after review."),
            "source_rule_id": rule["rule_id"],
        })
    return loaded


def safe_read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None

def included_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(root).parts
        if any(part in EXCLUDED_DIRS for part in rel_parts):
            continue
        # Source/config text formats only; avoid scanning binaries and generated artifacts.
        if path.suffix.lower() not in {
            ".py", ".xml", ".csv", ".js", ".mjs", ".ts", ".scss", ".css",
            ".json", ".yml", ".yaml", ".html", ".po", ".txt"
        } and path.name != "__manifest__.py":
            continue
        yield path

def rule_applies(rule, rel: str) -> bool:
    # Patterns deliberately allow a broad fallback when "**/*.ext" appears.
    import fnmatch
    return any(fnmatch.fnmatch(rel, glob) or fnmatch.fnmatch("/" + rel, glob) for glob in rule["globs"])

def load_rule_catalog() -> dict:
    """Load and validate the separate JSON migration rule files beside this scanner."""
    rules_dir = Path(__file__).resolve().parents[2] / "migration-rules"
    catalog = {"directory": "migration-rules", "files": [], "common_rule_count": 0,
               "transition_checks": {}, "transition_rule_counts": {}, "rule_ids": [], "load_errors": []}
    for filename in ("common.json", "16-to-17.json", "17-to-18.json", "18-to-19.json", "19-to-20.json"):
        path = rules_dir / filename
        if not path.is_file():
            catalog["load_errors"].append(f"Missing rule file: {filename}")
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            catalog["load_errors"].append(f"Invalid {filename}: {type(exc).__name__}: {exc}")
            continue
        catalog["files"].append(filename)
        if filename == "common.json":
            rules = data.get("rules", [])
            catalog["common_rule_count"] = len(rules)
            catalog["rule_ids"] = [r.get("rule_id") for r in rules if r.get("rule_id")]
            catalog["mandatory_rule_count"] = sum(1 for r in rules if r.get("mandatory_audit_check"))
        else:
            transition = f"{data.get('source_version', '?')}->{data.get('target_version', '?')}"
            catalog["transition_checks"][transition] = len(data.get("required_checks", []))
            catalog["transition_rule_counts"][transition] = len(data.get("rules", []))
    catalog["loaded"] = len(catalog["files"]) == 5 and not catalog["load_errors"]
    return catalog

def main() -> int:
    if len(sys.argv) != 2:
        print(json.dumps({
            "schema_version": SCHEMA_VERSION, "module": None,
            "source_version": SOURCE_VERSION, "target_version": TARGET_VERSION,
            "status": "failed", "command": "scanner.py", "exit_code": 2,
            "output_format": "json", "parse_status": "success",
            "summary": {"errors": 0, "warnings": 0, "info": 0, "findings": 0},
            "findings": [], "tests_run": [],
            "unresolved_risks": ["Usage: scanner.py <module_folder_name_or_path>"],
            "database_operations": []
        }, ensure_ascii=False))
        return 2

    module_arg = sys.argv[1]
    root = Path(module_arg).resolve()
    if not root.is_dir():
        print(json.dumps({
            "schema_version": SCHEMA_VERSION, "module": module_arg,
            "source_version": SOURCE_VERSION, "target_version": TARGET_VERSION,
            "status": "failed", "command": "audit.sh", "exit_code": 2,
            "output_format": "json", "parse_status": "success",
            "summary": {"errors": 0, "warnings": 0, "info": 0, "findings": 0},
            "findings": [], "tests_run": [],
            "unresolved_risks": ["Module directory does not exist or is not a directory."],
            "database_operations": []
        }, ensure_ascii=False))
        return 2

    findings = []
    file_count = 0
    json_rules = load_json_scanner_rules()
    active_rules = RULES + json_rules
    for path in included_files(root):
        text = safe_read(path)
        if text is None:
            continue
        file_count += 1
        rel = path.relative_to(root).as_posix()
        lines = text.splitlines()
        # A legacy ACL CSV filename is itself a mandatory Odoo 20 migration finding.
        if rel == "security/ir.model.access.csv":
            findings.append({"id": f"MANUAL-SEC-001-{len(findings)+1:04d}", "rule_id": "MANUAL-SEC-001", "category": "security", "severity": "error", "file": rel, "line": 1, "column": 1, "message": "Legacy security/ir.model.access.csv filename detected. Verify Odoo 20 expects security/ir.access.csv and migrate the combined access/record-rule semantics, CSV header, XML references and manifest load order.", "classification": "needs_investigation", "source_version": SOURCE_VERSION, "target_version": TARGET_VERSION, "transition": "19.0->20.0", "evidence": rel, "suggested_fix": "Do not merely rename the file. Compare old ACL and record-rule semantics with Odoo 20 ir.access, then propose a complete security-preserving conversion.", "risk": "Security-critical: avoid broadening access.", "confidence": "high", "verification": "requires_exact_target_source_confirmation", "approval": "not_requested"})
        for rule in active_rules:
            if not rule_applies(rule, rel):
                continue
            try:
                rx: Pattern[str] = re.compile(rule["pattern"])
            except re.error:
                continue
            for line_no, line in enumerate(lines, 1):
                for match in rx.finditer(line):
                    if rule.get("special") == "manifest_paths":
                        candidate = match.group(1)
                        # Skip obvious URLs and interpolation; manifest parsing is intentionally conservative.
                        if "://" in candidate or "${" in candidate:
                            continue
                        exists = (root / candidate).is_file()
                        if exists:
                            continue
                        message = f"Potential manifest-declared path does not exist: {candidate}"
                        evidence = line.strip()[:400]
                        suggested = "Confirm the path is intended and relative to the module root; remove or correct it only after reviewing manifest semantics."
                        severity = "warning"
                    else:
                        message = rule["message"]
                        evidence = line.strip()[:400]
                        suggested = rule["suggested_fix"]
                        severity = rule["severity"]
                    findings.append({
                        "id": f"{rule['id']}-{len(findings)+1:04d}",
                        "rule_id": rule.get("source_rule_id", rule["id"]),
                        "category": rule["category"],
                        "severity": severity,
                        "file": rel,
                        "line": line_no,
                        "column": match.start() + 1,
                        "message": message,
                        "classification": "needs_investigation",
                        "source_version": SOURCE_VERSION,
                        "target_version": TARGET_VERSION,
                        "transition": rule["transition"],
                        "evidence": evidence,
                        "suggested_fix": suggested,
                        "risk": "Do not edit based on this heuristic alone; verify against the exact Odoo 20 source and preserve behavior.",
                        "confidence": "low",
                        "verification": "unverified",
                        "approval": "not_requested"
                    })

    summary = {
        "errors": sum(1 for f in findings if f["severity"] == "error"),
        "warnings": sum(1 for f in findings if f["severity"] == "warning"),
        "info": sum(1 for f in findings if f["severity"] == "info"),
        "findings": len(findings),
        "files_scanned": file_count
    }
    status = "completed_with_findings" if findings else "completed"
    rule_catalog = load_rule_catalog()
    report = {
        "schema_version": SCHEMA_VERSION,
        "rule_catalog": rule_catalog,
        "module": root.name,
        "module_path": str(root),
        "source_version": SOURCE_VERSION,
        "target_version": TARGET_VERSION,
        "status": status,
        "command": "audit.sh " + module_arg,
        "exit_code": 0,
        "output_format": "json",
        "parse_status": "success",
        "summary": summary,
        "findings": findings,
        "tests_run": ["read-only source-pattern scan"],
        "unresolved_risks": ([
            "Pattern matches are heuristic leads, not verified Odoo 20 incompatibilities.",
            "No Odoo server, database, module installation, XML schema, Python runtime, or JavaScript build was executed.",
            "Transition-specific rules must be verified against official Odoo 20 documentation/source and the actual deployment edition."
        ] + (["Migration rule catalog could not be fully loaded: " + "; ".join(rule_catalog["load_errors"])] if rule_catalog["load_errors"] else [])),
        "database_operations": []
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    # Exit 0 means scan ran successfully, not that migration is compatible.
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({
            "schema_version": SCHEMA_VERSION,
            "module": sys.argv[1] if len(sys.argv) > 1 else None,
            "source_version": SOURCE_VERSION,
            "target_version": TARGET_VERSION,
            "status": "failed",
            "command": "audit.sh",
            "exit_code": 3,
            "output_format": "json",
            "parse_status": "success",
            "summary": {"errors": 0, "warnings": 0, "info": 0, "findings": 0},
            "findings": [],
            "tests_run": [],
            "unresolved_risks": [f"Scanner internal error: {type(exc).__name__}: {exc}"],
            "database_operations": []
        }, ensure_ascii=False, indent=2))
        raise SystemExit(3)
