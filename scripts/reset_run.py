from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _clear_generated_children(directory: Path) -> int:
    directory.mkdir(parents=True, exist_ok=True)
    removed = 0
    for child in directory.iterdir():
        if child.name == ".gitkeep":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
        removed += 1
    return removed


def reset_generated_artifacts(
    *,
    runs_dir: Path,
    normalized_dir: Path,
    site_dir: Path,
) -> dict[str, int]:
    return {
        "runs_removed": _clear_generated_children(runs_dir),
        "normalized_removed": _clear_generated_children(normalized_dir),
        "site_removed": _clear_generated_children(site_dir),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Clear generated OpenClaw Model Arena artifacts.")
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "runs",
        help="Directory containing raw run artifacts.",
    )
    parser.add_argument(
        "--normalized-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "normalized",
        help="Directory containing normalized run artifacts.",
    )
    parser.add_argument(
        "--site-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "site",
        help="Directory containing generated site artifacts.",
    )
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    summary = reset_generated_artifacts(
        runs_dir=args.runs_dir,
        normalized_dir=args.normalized_dir,
        site_dir=args.site_dir,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
