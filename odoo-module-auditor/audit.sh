#!/usr/bin/env bash
set -euo pipefail

# Read-only, JSON-only heuristic scanner for Odoo 16 -> Odoo 20.
# Intended path: <repository-root>/odoo-module-auditor/audit.sh
# Exit 0 = scan completed (not proof of compatibility).
# Exit 2 = usage/module path error. Exit 3 = scanner error.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SCANNER="${SCRIPT_DIR}/scripts/odoo-audit/scanner.py"

if [[ $# -lt 1 || $# -gt 2 ]]; then
  printf 'Usage: %s <module_folder_name_or_path> [--format=json]\n' "$0" >&2
  exit 2
fi

MODULE="$1"
if [[ $# -eq 2 && "$2" != "--format=json" ]]; then
  printf 'Only supported optional argument: --format=json (JSON is the default)\n' >&2
  exit 2
fi

if [[ ! -f "$SCANNER" ]]; then
  printf 'Scanner not found: %s\n' "$SCANNER" >&2
  exit 3
fi

exec python3 "$SCANNER" "$MODULE"
