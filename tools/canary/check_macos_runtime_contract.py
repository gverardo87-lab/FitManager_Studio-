"""Emit the falsifiable G-MAC.1 runtime coupling report for C0.1."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def evaluate_runtime_contract(
    *,
    target_system: str,
    frpc_filename: str,
    acme_client_filename: str,
) -> dict[str, object]:
    expected = {
        "Windows": {"frpc": "frpc.exe", "acme": "lego.exe"},
        "Darwin": {"frpc": "frpc", "acme": "lego"},
    }
    if target_system not in expected:
        raise ValueError(f"Target non supportato dal contratto: {target_system}")

    actual = {"frpc": frpc_filename, "acme": acme_client_filename}
    findings = []
    for component, expected_filename in expected[target_system].items():
        if actual[component] != expected_filename:
            findings.append(
                {
                    "code": f"G-MAC.1-{component.upper()}-FILENAME",
                    "component": component,
                    "expected": expected_filename,
                    "actual": actual[component],
                }
            )
    return {
        "schema": 1,
        "target_system": target_system,
        "result": "PASS" if not findings else "RED",
        "findings": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-system", choices=("Darwin", "Windows"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    # Importing api.config must never create a secret during a technical audit.
    os.environ.setdefault("JWT_SECRET", "c0-runtime-contract-no-production-secret")
    from api.services import tunnel_config

    report = evaluate_runtime_contract(
        target_system=args.target_system,
        frpc_filename=tunnel_config._FRPC_FILENAME,
        acme_client_filename=tunnel_config._ACME_CLIENT_FILENAME,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"result": report["result"], "finding_count": len(report["findings"])}))
    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
