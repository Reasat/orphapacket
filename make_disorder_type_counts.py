#!/usr/bin/env python3
"""
Generate a two-column table of DisorderType counts from ORPHApacket JSON files.

Outputs:
- disorder_type_counts.csv (columns: DisorderType_Value, Count)
- disorder_type_counts.md (markdown table)

Usage:
  python make_disorder_type_counts.py [json_directory]

Default json_directory is "json" relative to repo root.
"""

import sys
import os
import glob
import json
from collections import Counter


def collect_disorder_type_counts(json_directory: str) -> Counter:
    json_pattern = os.path.join(json_directory, "ORPHApacket_*.json")
    counts: Counter = Counter()

    files = glob.glob(json_pattern)
    total = len(files)
    processed = 0

    for path in files:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            disorder_type = (
                data.get("Orphapacket", {})
                .get("DisorderType", {})
                .get("value")
            )
            if disorder_type:
                counts[disorder_type] += 1
            processed += 1
            if processed % 2000 == 0:
                print(f"Processed {processed}/{total} files...")
        except Exception as exc:
            print(f"Warning: failed to parse {path}: {exc}")

    return counts


def write_csv(counts: Counter, csv_path: str) -> None:
    lines = ["DisorderType_Value,Count"]
    for value, count in counts.most_common():
        # Escape commas in value by quoting if necessary
        if "," in value:
            safe_value = '"' + value.replace('"', '""') + '"'
        else:
            safe_value = value
        lines.append(f"{safe_value},{count}")
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def write_markdown(counts: Counter, md_path: str) -> None:
    lines = [
        "| DisorderType Value | Count |",
        "|---|---:",
    ]
    for value, count in counts.most_common():
        lines.append(f"| {value} | {count} |")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main() -> None:
    json_directory = sys.argv[1] if len(sys.argv) > 1 else "json"
    print(f"Scanning JSON files in: {json_directory}")
    counts = collect_disorder_type_counts(json_directory)

    if not counts:
        print("No DisorderType values found.")
        sys.exit(1)

    csv_path = "disorder_type_counts.csv"
    md_path = "disorder_type_counts.md"
    write_csv(counts, csv_path)
    write_markdown(counts, md_path)

    print("\nGenerated files:")
    print(f" - {csv_path}")
    print(f" - {md_path}")


if __name__ == "__main__":
    main()


