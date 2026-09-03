"""Audit and inventory the wheelhouse used by the macOS C0 portability canary."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

SQLCIPHER_ARM64_WHEEL = "sqlcipher3-0.6.2-cp312-cp312-macosx_11_0_arm64.whl"
SQLCIPHER_ARM64_SHA256 = "bc2edd981e65783bc0d4e337704a9eb436871ab91c68af02ed76354876087642"


def _wheel_tags(path: Path) -> list[str]:
    with ZipFile(path) as archive:
        metadata_path = next(
            (name for name in archive.namelist() if name.endswith(".dist-info/WHEEL")),
            None,
        )
        if metadata_path is None:
            raise ValueError(f"WHEEL metadata assente: {path.name}")
        metadata = archive.read(metadata_path).decode("utf-8")
    return sorted(
        line.removeprefix("Tag:").strip()
        for line in metadata.splitlines()
        if line.startswith("Tag:")
    )


def _tag_is_arm64_safe(tag: str) -> bool:
    parts = tag.split("-", maxsplit=2)
    if len(parts) != 3:
        return False
    platform_tag = parts[2]
    if platform_tag == "any":
        return True
    return any(
        candidate.endswith("_arm64") or candidate.endswith("_universal2")
        for candidate in platform_tag.split(".")
    )


def build_manifest(wheelhouse: Path) -> dict[str, object]:
    wheels = sorted(wheelhouse.glob("*.whl"))
    if not wheels:
        raise ValueError("Wheelhouse vuota")

    entries: list[dict[str, object]] = []
    findings: list[str] = []
    for wheel in wheels:
        digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
        tags = _wheel_tags(wheel)
        if not tags or not all(_tag_is_arm64_safe(tag) for tag in tags):
            findings.append(f"WHEEL_TAG_NON_ARM64:{wheel.name}")
        if wheel.name == SQLCIPHER_ARM64_WHEEL and digest != SQLCIPHER_ARM64_SHA256:
            findings.append("SQLCIPHER_SHA256_MISMATCH")
        entries.append(
            {
                "file": wheel.name,
                "sha256": digest,
                "size_bytes": wheel.stat().st_size,
                "tags": tags,
            }
        )

    sqlcipher_entries = [entry for entry in entries if str(entry["file"]).lower().startswith("sqlcipher3-")]
    if [entry["file"] for entry in sqlcipher_entries] != [SQLCIPHER_ARM64_WHEEL]:
        findings.append("SQLCIPHER_ARM64_WHEEL_NOT_EXACT")

    return {
        "schema": 1,
        "architecture_policy": "pure-python-or-macos-arm64-compatible-input",
        "final_artifact_policy": "mach-o-arm64-only-after-thinning-and-codesign",
        "result": "PASS" if not findings else "FAIL",
        "findings": sorted(findings),
        "wheels": entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("wheelhouse", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    manifest = build_manifest(args.wheelhouse)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"result": manifest["result"], "wheel_count": len(manifest["wheels"])}))
    return 0 if manifest["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
