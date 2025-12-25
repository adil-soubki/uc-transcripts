#!/usr/bin/env python3
"""
Clean up malformed category assignments in parsed question data.

This script fixes issues where gpt-5-mini concatenated primary and secondary
categories with semicolons instead of properly splitting them.
"""

import json
import glob
from pathlib import Path
import argparse
from collections import Counter
from typing import Dict, List, Tuple, Optional


# Category taxonomy: primary → list of secondaries (single source of truth)
CATEGORY_TAXONOMY = {
    "Literature": [
        "American Literature", "British Literature", "Classical Literature",
        "European Literature", "World Literature", "Other Literature", "Drama",
        "Long Fiction", "Poetry", "Short Fiction", "Misc Literature"
    ],
    "History": [
        "American History", "Ancient History", "European History", "Asian History",
        "British History", "World History", "Other History"
    ],
    "Science": [
        "Biology", "Chemistry", "Physics", "Other Science", "Math", "Mathematics",
        "Astronomy", "Computer Science", "Earth Science", "Engineering", "Misc Science"
    ],
    "Fine Arts": [
        "Visual Fine Arts", "Auditory Fine Arts", "Other Fine Arts",
        "Architecture", "Dance", "Film", "Jazz", "Musicals", "Opera",
        "Photography", "Misc Arts"
    ],
    "RMPSS": [
        "Religion", "Mythology", "Philosophy", "Social Science", "Anthropology",
        "Economics", "Linguistics", "Language", "Psychology", "Sociology",
        "Other Social Science", "Politics"
    ],
    "Other": [
        "Movies", "Music", "Sports", "Television", "Video Games", "Other Pop Culture",
        "Geography", "Current Events", "Other Academic"
    ]
}

# Derived sets
VALID_PRIMARIES = set(CATEGORY_TAXONOMY.keys())
KNOWN_SECONDARIES = set(sec for secs in CATEGORY_TAXONOMY.values() for sec in secs)


def parse_category(primary_str: Optional[str], secondary_list: Optional[List[str]]) -> Tuple[Optional[str], List[str]]:
    """
    Parse and clean a category assignment.

    Returns:
        (cleaned_primary, cleaned_secondary_list)
    """
    if not primary_str:
        return None, []

    # Handle None secondary list or string instead of list
    if secondary_list is None:
        secondary_list = []
    elif isinstance(secondary_list, str):
        # If it's a string instead of a list, convert it
        secondary_list = [secondary_list]

    # Split by semicolon if present
    parts = [p.strip() for p in primary_str.split(";")]

    cleaned_primary = None
    cleaned_secondary = list(secondary_list)  # Start with existing secondaries

    # Find the valid primary category
    for part in parts:
        if part in VALID_PRIMARIES:
            cleaned_primary = part
        elif part in KNOWN_SECONDARIES and part not in cleaned_secondary:
            # This should be a secondary, not primary
            cleaned_secondary.append(part)
        elif part:
            # Unknown category - could be a valid secondary we don't know about
            # Add it to secondaries if not already there
            if part not in cleaned_secondary:
                cleaned_secondary.append(part)

    # If we didn't find a valid primary but we have parts, try to infer it
    if not cleaned_primary and parts:
        first_part = parts[0]

        # Check if first part is a known secondary - infer primary from it
        if first_part in KNOWN_SECONDARIES:
            cleaned_primary = infer_primary_from_secondary(first_part)
            if first_part not in cleaned_secondary:
                cleaned_secondary.append(first_part)
        else:
            # Keep the original if we can't clean it
            cleaned_primary = primary_str

    # BEGIN : ADIL ADDED
    # TODO: Split the ones with ";" in them.
    current_secondary = cleaned_secondary
    cleaned_secondary = []
    for secondary_str in current_secondary:
        if secondary_str is None:
            continue
        secondary_parts = [p.strip() for p in secondary_str.split(";")]
        for part in secondary_parts:
            if part == cleaned_primary:
                continue  # Skip if this category matches the primary.
            cleaned_secondary.append(part)
    # END   : ADIL ADDED

    return cleaned_primary, cleaned_secondary


def infer_primary_from_secondary(secondary: str) -> Optional[str]:
    """Infer the primary category from a secondary category."""
    for primary, secondaries in CATEGORY_TAXONOMY.items():
        if secondary in secondaries:
            return primary
    return None


def clean_question_category(question: Dict) -> bool:
    """
    Clean the category of a single question.

    Returns:
        True if the category was modified, False otherwise
    """
    category = question.get("category")
    if not category:
        return False

    original_primary = category.get("primary")
    original_secondary = category.get("secondary")

    cleaned_primary, cleaned_secondary = parse_category(original_primary, original_secondary)

    # Update the category
    modified = False
    if cleaned_primary != original_primary:
        category["primary"] = cleaned_primary
        modified = True

    if cleaned_secondary != original_secondary:
        category["secondary"] = cleaned_secondary if cleaned_secondary else None
        modified = True

    return modified


def clean_episode_file(file_path: str, dry_run: bool = False, track_changes: Optional[Dict] = None) -> Tuple[int, int]:
    """
    Clean categories in a single episode file.

    Returns:
        (total_questions, modified_questions)
    """
    with open(file_path, "r") as f:
        data = json.load(f)

    total_questions = len(data.get("questions", []))
    modified_count = 0

    for question in data.get("questions", []):
        # Track changes if requested
        if track_changes is not None:
            category = question.get("category", {})
            original_primary = category.get("primary")
            original_secondary = category.get("secondary")

            if clean_question_category(question):
                modified_count += 1
                new_primary = category.get("primary")
                new_secondary = category.get("secondary")

                # Normalize secondary to list for comparison
                orig_sec_normalized = original_secondary if isinstance(original_secondary, list) else ([original_secondary] if original_secondary else [])
                new_sec_normalized = new_secondary if isinstance(new_secondary, list) else ([new_secondary] if new_secondary else [])

                # Track the transformation
                before = (original_primary, tuple(orig_sec_normalized) if orig_sec_normalized else None)
                after = (new_primary, tuple(new_sec_normalized) if new_sec_normalized else None)

                if before not in track_changes:
                    track_changes[before] = []
                if after not in track_changes[before]:
                    track_changes[before].append(after)
        else:
            if clean_question_category(question):
                modified_count += 1

    # Save the cleaned data
    if not dry_run and modified_count > 0:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

    return total_questions, modified_count


def analyze_categories(data_path: str):
    """Analyze category issues before cleaning."""
    print("Analyzing category assignments...\n")

    malformed_primaries = Counter()
    valid_primaries = Counter()
    none_primaries = 0

    files = glob.glob(f"{data_path}/*.json")

    for file_path in files:
        with open(file_path, "r") as f:
            data = json.load(f)

        for question in data.get("questions", []):
            category = question.get("category", {})
            primary = category.get("primary")

            if not primary:
                none_primaries += 1
                continue

            if primary in VALID_PRIMARIES:
                valid_primaries[primary] += 1
            else:
                malformed_primaries[primary] += 1

    print(f"Valid primary categories: {sum(valid_primaries.values())}")
    for cat, count in valid_primaries.most_common():
        print(f"  {cat}: {count}")

    print(f"\nMalformed primary categories: {sum(malformed_primaries.values())}")
    for cat, count in malformed_primaries.most_common(30):
        print(f"  {cat}: {count}")

    print(f"\nQuestions with None/missing primary: {none_primaries}")


def main():
    parser = argparse.ArgumentParser(
        description="Clean up malformed category assignments in parsed questions"
    )
    parser.add_argument(
        "--data-path",
        default="./data/questions/gpt-5-mini",
        help="Path to parsed question data (default: ./data/questions/gpt-5-mini)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying files"
    )
    parser.add_argument(
        "--analyze-only",
        action="store_true",
        help="Only analyze category issues, don't clean"
    )
    parser.add_argument(
        "--output-path",
        help="Output to a different directory instead of modifying in place"
    )
    parser.add_argument(
        "--show-changes",
        action="store_true",
        help="Show all unique category transformations (works with or without dry-run)"
    )

    args = parser.parse_args()

    # Analyze categories
    if args.analyze_only:
        analyze_categories(args.data_path)
        return

    # Get all episode files
    files = glob.glob(f"{args.data_path}/*.json")
    print(f"Found {len(files)} episode files")

    # Track changes if dry-run or show-changes is requested
    changes_tracker = {} if (args.dry_run or args.show_changes) else None

    # Clean each file
    total_questions = 0
    total_modified = 0

    for file_path in files:
        # Determine output path
        if args.output_path:
            Path(args.output_path).mkdir(parents=True, exist_ok=True)
            output_file = str(Path(args.output_path) / Path(file_path).name)

            # Copy to output path first
            with open(file_path, "r") as f:
                data = json.load(f)
            with open(output_file, "w") as f:
                json.dump(data, f, indent=2)

            file_to_clean = output_file
        else:
            file_to_clean = file_path

        q_count, m_count = clean_episode_file(file_to_clean, dry_run=args.dry_run, track_changes=changes_tracker)
        total_questions += q_count
        total_modified += m_count

    # Print summary
    print(f"\nProcessed {total_questions} questions across {len(files)} episodes")
    print(f"Modified {total_modified} questions ({(total_modified/total_questions*100):.1f}%)")

    # Show unique transformations if dry-run or show-changes
    if changes_tracker:
        print("\n" + "="*80)
        print("UNIQUE CATEGORY TRANSFORMATIONS")
        print("="*80 + "\n")

        # Sort with None-safe key
        def sort_key(item):
            before_primary, before_secondary = item[0]
            # Convert None to empty string for sorting
            primary_key = before_primary if before_primary else ""
            # Convert None elements in tuple to empty strings
            if before_secondary:
                secondary_key = tuple(s if s else "" for s in before_secondary)
            else:
                secondary_key = ()
            return (primary_key, secondary_key)

        sorted_items = sorted(changes_tracker.items(), key=sort_key)

        for before, afters in sorted_items:
            before_primary, before_secondary = before
            before_sec_list = list(before_secondary) if before_secondary else []

            print(f"BEFORE: primary=\"{before_primary}\", secondary={before_sec_list}")

            for after in afters:
                after_primary, after_secondary = after
                after_sec_list = list(after_secondary) if after_secondary else []
                print(f" AFTER: primary=\"{after_primary}\", secondary={after_sec_list}")
            print()

    if args.dry_run:
        print("\n(Dry run - no files were actually modified)")
    elif args.output_path:
        print(f"\nCleaned files saved to: {args.output_path}")
    else:
        print("\nFiles updated in place")

    # Show analysis after cleaning if not dry run
    if not args.dry_run:
        print("\n" + "="*80)
        print("Category distribution after cleaning:")
        print("="*80 + "\n")
        analyze_categories(args.output_path if args.output_path else args.data_path)


if __name__ == "__main__":
    main()
