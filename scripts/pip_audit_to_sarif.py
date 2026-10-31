"""Convert pip-audit JSON report to SARIF v2.1.0 format."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def convert(input_path: str, output_path: str) -> None:
    in_file = Path(input_path)
    dependencies: list[dict] = []
    if in_file.is_file():
        try:
            raw = json.loads(in_file.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                dependencies = raw.get("dependencies", [])
            elif isinstance(raw, list):
                dependencies = raw
        except Exception:
            dependencies = []

    rules: list[dict] = []
    results: list[dict] = []
    rule_ids: set[str] = set()

    for dep in dependencies:
        pkg_name = dep.get("name", "unknown")
        pkg_version = dep.get("version", "unknown")
        vulns = dep.get("vulns", [])
        for vuln in vulns:
            vid = vuln.get("id", "VULN-UNKNOWN")
            desc = vuln.get("description", f"Vulnerability in {pkg_name} {pkg_version}")
            fix_versions = vuln.get("fix_versions", [])

            if vid not in rule_ids:
                rule_ids.add(vid)
                rules.append(
                    {
                        "id": vid,
                        "name": f"Vulnerability_{vid.replace('-', '_')}",
                        "shortDescription": {"text": f"Vulnerability {vid} in {pkg_name}"},
                        "fullDescription": {"text": desc},
                        "help": {
                            "text": f"Package: {pkg_name} {pkg_version}\nFix versions: {', '.join(fix_versions) if fix_versions else 'None available'}"
                        },
                        "properties": {
                            "security-severity": "7.5",
                            "tags": ["security", "vulnerability", "dependencies"],
                        },
                    }
                )

            results.append(
                {
                    "ruleId": vid,
                    "message": {
                        "text": f"Package {pkg_name}@{pkg_version} has known vulnerability {vid}. Upgrade to {', '.join(fix_versions) if fix_versions else 'patched version'}."
                    },
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {"uri": "pyproject.toml"},
                                "region": {"startLine": 1},
                            }
                        }
                    ],
                }
            )

    sarif = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "pip-audit",
                        "informationUri": "https://github.com/pypa/pip-audit",
                        "version": "2.7.3",
                        "rules": rules,
                    }
                },
                "results": results,
            }
        ],
    }

    Path(output_path).write_text(json.dumps(sarif, indent=2), encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python pip_audit_to_sarif.py <input.json> <output.sarif>")
        sys.exit(1)
    convert(sys.argv[1], sys.argv[2])
