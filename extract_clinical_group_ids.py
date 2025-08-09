#!/usr/bin/env python3
"""
Extract ORPHA IDs that have DisorderType "Clinical group" from ORPHApacket JSON files.

Outputs:
- clinical_group_orpha_ids.csv (columns: ORPHAcode, Label)

Usage:
  python extract_clinical_group_ids.py [json_directory]

Default json_directory is "json" relative to repo root.
"""

import sys
import os
import glob
import json
import csv


def extract_clinical_group_ids(json_directory: str) -> list:
    """Extract ORPHA IDs and labels for entries with DisorderType 'Clinical group'."""
    json_pattern = os.path.join(json_directory, "ORPHApacket_*.json")
    clinical_group_entries = []

    files = glob.glob(json_pattern)
    total = len(files)
    processed = 0

    for path in files:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            orphapacket = data.get("Orphapacket", {})
            disorder_type = orphapacket.get("DisorderType", {}).get("value")
            
            if disorder_type == "Clinical group":
                orpha_code = orphapacket.get("ORPHAcode")
                label = orphapacket.get("Label")
                
                if orpha_code and label:
                    clinical_group_entries.append({
                        "ORPHAcode": orpha_code,
                        "Label": label
                    })
            
            processed += 1
            if processed % 2000 == 0:
                print(f"Processed {processed}/{total} files...")
                
        except Exception as exc:
            print(f"Warning: failed to parse {path}: {exc}")

    return clinical_group_entries


def write_csv(entries: list, csv_path: str) -> None:
    """Write the clinical group entries to a CSV file."""
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["ORPHAcode", "Label"])
        writer.writeheader()
        
        # Sort by ORPHAcode for consistent output
        sorted_entries = sorted(entries, key=lambda x: int(x["ORPHAcode"]))
        writer.writerows(sorted_entries)


def main() -> None:
    json_directory = sys.argv[1] if len(sys.argv) > 1 else "json"
    print(f"Scanning JSON files in: {json_directory}")
    print("Looking for DisorderType: 'Clinical group'...")
    
    clinical_group_entries = extract_clinical_group_ids(json_directory)

    if not clinical_group_entries:
        print("No Clinical group entries found.")
        sys.exit(1)

    csv_path = "clinical_group_orpha_ids.csv"
    write_csv(clinical_group_entries, csv_path)

    print(f"\nFound {len(clinical_group_entries)} Clinical group entries")
    print(f"Generated file: {csv_path}")
    
    # Show first few entries as preview
    if clinical_group_entries:
        print("\nFirst 5 entries:")
        for i, entry in enumerate(clinical_group_entries[:5]):
            print(f"  {i+1}. ORPHA:{entry['ORPHAcode']} - {entry['Label']}")


if __name__ == "__main__":
    main()
