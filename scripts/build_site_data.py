from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from benchmark.site_payload import build_site_payload


def _load_normalized_runs(normalized_dir: Path) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    for path in sorted(
        candidate
        for candidate in normalized_dir.rglob("*.json")
        if "transcripts" not in candidate.parts
    ):
        payload = json.loads(path.read_text())
        if isinstance(payload, dict):
            runs.append(payload)
    return runs


def build_site_data(*, normalized_dir: Path, output_path: Path) -> dict[str, Any]:
    payload = build_site_payload(_load_normalized_runs(normalized_dir))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    project_site_dir = (PROJECT_ROOT / "data" / "site").resolve()
    if output_path.resolve().parent == project_site_dir:
        public_output_path = PROJECT_ROOT / "app" / "public" / "site-data.json"
        public_output_path.parent.mkdir(parents=True, exist_ok=True)
        public_output_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return payload


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build site data from normalized runs.")
    parser.add_argument(
        "--normalized-dir",
        type=Path,
        default=Path("Projects/openclaw-model-arena/data/normalized"),
        help="Directory containing normalized run JSON files.",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=Path("Projects/openclaw-model-arena/data/site/site-data.json"),
        help="Destination JSON file for site payload data.",
    )
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    build_site_data(normalized_dir=args.normalized_dir, output_path=args.output_path)


if __name__ == "__main__":
    main()
