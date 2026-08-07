"""Build a sanitized manifest for the source-free C0 canary package."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
import subprocess
from pathlib import Path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _directory_size(path: Path) -> int:
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-root", required=True, type=Path)
    parser.add_argument("--wheel-manifest", required=True, type=Path)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    backend = args.package_root / "backend" / "fitmanager-c0-canary"
    node = args.package_root / "node" / "bin" / "node"
    frontend_server = args.package_root / "frontend" / "server.js"
    for required in (backend, node, frontend_server, args.wheel_manifest):
        if not required.exists():
            raise FileNotFoundError(required.name)

    node_version = subprocess.run(
        [str(node), "--version"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    manifest = {
        "schema": 1,
        "source_commit": args.source_commit,
        "build": {
            "architecture": platform.machine().lower(),
            "os": platform.system(),
            "os_version": platform.mac_ver()[0],
            "python": platform.python_version(),
            "node": node_version,
            "nuitka": importlib.metadata.version("Nuitka"),
        },
        "artifacts": {
            "backend_sha256": _sha256(backend),
            "node_sha256": _sha256(node),
            "package_size_bytes": _directory_size(args.package_root),
        },
        "wheelhouse": json.loads(args.wheel_manifest.read_text(encoding="utf-8")),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"result": "PASS", "package_size_bytes": manifest["artifacts"]["package_size_bytes"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
