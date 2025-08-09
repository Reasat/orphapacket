#!/usr/bin/env python3
"""
JSON Structure Analysis Script

Analyzes all ORPHApacket JSON files to identify all keys and nested keys present
in the dataset, with frequency counts and examples.
"""

import json
import glob
import os
from collections import defaultdict, Counter
import pandas as pd

def extract_keys_recursive(obj, path="", key_structure=None):
    """
    Recursively extract all keys and nested keys from a JSON object.
    
    Args:
        obj: JSON object (dict, list, or primitive)
        path: Current path in the JSON structure
        key_structure: Dictionary to store key paths and their counts
    
    Returns:
        dict: Key structure with paths and counts
    """
    if key_structure is None:
        key_structure = defaultdict(int)
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            current_path = f"{path}.{key}" if path else key
            key_structure[current_path] += 1
            
            # Recursively analyze nested structures
            extract_keys_recursive(value, current_path, key_structure)
    
    elif isinstance(obj, list):
        if obj:  # Only analyze non-empty lists
            # Analyze the structure of list items
            for i, item in enumerate(obj[:3]):  # Sample first 3 items
                list_path = f"{path}[{i}]" if i < 3 else f"{path}[...]"
                extract_keys_recursive(item, list_path, key_structure)
    
    return key_structure

def analyze_json_files(json_directory):
    """
    Analyze all JSON files in the directory to extract key structures.
    
    Args:
        json_directory (str): Path to directory containing JSON files
        
    Returns:
        dict: Analysis results
    """
    json_files = glob.glob(os.path.join(json_directory, "ORPHApacket_*.json"))
    total_files = len(json_files)
    
    print(f"🔍 Analyzing JSON structure across {total_files:,} files...")
    
    # Collect all key structures
    all_key_structures = defaultdict(int)
    sample_values = defaultdict(list)
    file_examples = defaultdict(list)
    
    processed = 0
    
    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract key structure from this file
            file_key_structure = extract_keys_recursive(data)
            
            # Add to overall structure
            for key_path, count in file_key_structure.items():
                all_key_structures[key_path] += 1
                
                # Store example file for this key path
                if len(file_examples[key_path]) < 3:
                    file_examples[key_path].append(os.path.basename(json_file))
                
                # Store sample values for leaf keys (non-nested)
                if len(sample_values[key_path]) < 5:
                    try:
                        # Navigate to the value using the key path
                        current_obj = data
                        path_parts = key_path.split('.')
                        
                        for part in path_parts:
                            if '[' in part:  # Handle list indices
                                key_name = part.split('[')[0]
                                if key_name in current_obj and isinstance(current_obj[key_name], list):
                                    if current_obj[key_name]:
                                        current_obj = current_obj[key_name][0]
                                    else:
                                        break
                            else:
                                if part in current_obj:
                                    current_obj = current_obj[part]
                                else:
                                    break
                        
                        # Store sample value if it's a primitive type
                        if not isinstance(current_obj, (dict, list)):
                            if str(current_obj) not in sample_values[key_path]:
                                sample_values[key_path].append(str(current_obj))
                    except:
                        pass
            
            processed += 1
            if processed % 1000 == 0:
                print(f"Processed {processed:,}/{total_files:,} files...")
                
        except Exception as e:
            print(f"Error processing {json_file}: {str(e)}")
            continue
    
    print(f"✅ Analysis complete: {processed:,} files processed")
    
    return {
        'key_structures': dict(all_key_structures),
        'sample_values': dict(sample_values),
        'file_examples': dict(file_examples),
        'total_files': processed
    }

def generate_structure_report(analysis_results):
    """
    Generate a comprehensive report of the JSON structure analysis.
    
    Args:
        analysis_results (dict): Results from analyze_json_files
    """
    key_structures = analysis_results['key_structures']
    sample_values = analysis_results['sample_values']
    file_examples = analysis_results['file_examples']
    total_files = analysis_results['total_files']
    
    # Sort keys by frequency (most common first)
    sorted_keys = sorted(key_structures.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\n📊 JSON STRUCTURE ANALYSIS REPORT")
    print("=" * 80)
    print(f"Total files analyzed: {total_files:,}")
    print(f"Unique key paths found: {len(sorted_keys):,}")
    print("\n")
    
    # Group keys by depth level
    depth_groups = defaultdict(list)
    for key_path, count in sorted_keys:
        depth = key_path.count('.')
        depth_groups[depth].append((key_path, count))
    
    # Generate report by depth level
    for depth in sorted(depth_groups.keys()):
        print(f"🔸 DEPTH LEVEL {depth} ({len(depth_groups[depth])} keys)")
        print("-" * 60)
        
        for key_path, count in depth_groups[depth][:20]:  # Top 20 per level
            percentage = (count / total_files) * 100
            print(f"{key_path:<50} {count:>6,} ({percentage:>5.1f}%)")
            
            # Show sample values if available
            if key_path in sample_values and sample_values[key_path]:
                samples = sample_values[key_path][:3]
                print(f"{'':>50} Examples: {', '.join(samples)}")
            
            print()
        
        if len(depth_groups[depth]) > 20:
            print(f"... and {len(depth_groups[depth]) - 20} more keys at this depth\n")
        
        print()
    
    return sorted_keys

def export_to_csv(analysis_results):
    """
    Export the analysis results to CSV files.
    
    Args:
        analysis_results (dict): Results from analyze_json_files
    """
    key_structures = analysis_results['key_structures']
    sample_values = analysis_results['sample_values']
    file_examples = analysis_results['file_examples']
    total_files = analysis_results['total_files']
    
    # Prepare data for CSV
    csv_data = []
    for key_path, count in key_structures.items():
        percentage = (count / total_files) * 100
        depth = key_path.count('.')
        
        csv_data.append({
            'Key_Path': key_path,
            'Count': count,
            'Percentage': round(percentage, 2),
            'Depth': depth,
            'Sample_Values': '; '.join(sample_values.get(key_path, [])[:5]),
            'Example_Files': '; '.join(file_examples.get(key_path, [])[:3])
        })
    
    # Sort by count (descending)
    csv_data.sort(key=lambda x: x['Count'], reverse=True)
    
    # Export to CSV
    df = pd.DataFrame(csv_data)
    df.to_csv('json_structure_analysis.csv', index=False)
    
    # Export summary by depth
    depth_summary = defaultdict(lambda: {'count': 0, 'keys': []})
    for item in csv_data:
        depth = item['Depth']
        depth_summary[depth]['count'] += 1
        depth_summary[depth]['keys'].append(item['Key_Path'])
    
    summary_data = []
    for depth in sorted(depth_summary.keys()):
        summary_data.append({
            'Depth_Level': depth,
            'Number_of_Keys': depth_summary[depth]['count'],
            'Sample_Keys': '; '.join(depth_summary[depth]['keys'][:5])
        })
    
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv('json_structure_summary.csv', index=False)
    
    print("📁 Files exported:")
    print("   - json_structure_analysis.csv (detailed key analysis)")
    print("   - json_structure_summary.csv (summary by depth)")

def main():
    """Main function to run the JSON structure analysis."""
    print("🔍 JSON STRUCTURE ANALYZER")
    print("=" * 50)
    
    json_directory = "json"
    
    if not os.path.exists(json_directory):
        print(f"❌ Error: Directory '{json_directory}' not found!")
        return
    
    # Analyze JSON structure
    analysis_results = analyze_json_files(json_directory)
    
    # Generate report
    sorted_keys = generate_structure_report(analysis_results)
    
    # Export to CSV
    export_to_csv(analysis_results)
    
    # Print top-level summary
    print(f"\n🎯 TOP 10 MOST COMMON KEY PATHS:")
    print("-" * 50)
    for i, (key_path, count) in enumerate(sorted_keys[:10], 1):
        percentage = (count / analysis_results['total_files']) * 100
        print(f"{i:2d}. {key_path:<40} {count:>6,} ({percentage:>5.1f}%)")

if __name__ == "__main__":
    main()
