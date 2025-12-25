#!/usr/bin/env python3
"""
Topic modeling and analysis for parsed University Challenge transcripts.

This script analyzes parsed question data to identify:
- Common topics using LDA topic modeling
- Most frequent answers
- Category distributions
- Answer patterns by category
"""

import json
import glob
from pathlib import Path
from collections import Counter, defaultdict
from typing import List, Dict, Any
import argparse

import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation, NMF
import numpy as np


def load_all_questions(data_path: str) -> List[Dict[str, Any]]:
    """Load all questions from parsed JSON files."""
    questions = []
    files = glob.glob(f"{data_path}/*.json")

    print(f"Loading {len(files)} episode files...")

    for file_path in files:
        with open(file_path, "r") as f:
            episode_data = json.load(f)
            for question in episode_data.get("questions", []):
                # Add episode metadata to each question for context
                question["episode_info"] = episode_data.get("episode", {})
                questions.append(question)

    print(f"Loaded {len(questions)} total questions")
    return questions


def extract_question_texts(questions: List[Dict[str, Any]]) -> List[str]:
    """Extract all question text from questions, including bonus parts."""
    texts = []

    for q in questions:
        if q.get("type") == "starter" and q.get("question_text"):
            texts.append(q["question_text"])
        elif q.get("type") == "bonus":
            # Combine intro and parts
            parts_text = []
            if q.get("intro_text"):
                parts_text.append(q["intro_text"])
            for part in q.get("parts", []):
                if part.get("text"):
                    parts_text.append(part["text"])
            if parts_text:
                texts.append(" ".join(parts_text))

    return texts


def extract_answers(questions: List[Dict[str, Any]]) -> List[str]:
    """Extract all correct answers."""
    answers = []

    for q in questions:
        if q.get("type") == "starter" and q.get("correct_answer"):
            answers.append(q["correct_answer"])
        elif q.get("type") == "bonus":
            for part in q.get("parts", []):
                if part.get("correct_answer"):
                    answers.append(part["correct_answer"])

    return answers


def perform_topic_modeling(texts: List[str], n_topics: int = 10, method: str = "lda"):
    """Perform topic modeling on question texts."""
    print(f"\n{'='*80}")
    print(f"TOPIC MODELING ({method.upper()}, {n_topics} topics)")
    print(f"{'='*80}\n")

    # Use TF-IDF vectorization
    vectorizer = TfidfVectorizer(
        max_features=1000,
        min_df=5,  # Ignore terms that appear in fewer than 5 documents
        max_df=0.7,  # Ignore terms that appear in more than 70% of documents
        stop_words='english',
        ngram_range=(1, 2)  # Include bigrams
    )

    doc_term_matrix = vectorizer.fit_transform(texts)
    feature_names = vectorizer.get_feature_names_out()

    # Fit topic model
    if method == "lda":
        model = LatentDirichletAllocation(
            n_components=n_topics,
            random_state=42,
            max_iter=20
        )
    else:  # NMF
        model = NMF(
            n_components=n_topics,
            random_state=42,
            max_iter=200
        )

    model.fit(doc_term_matrix)

    # Display topics
    print(f"Top {n_topics} topics with their most relevant terms:\n")
    for topic_idx, topic in enumerate(model.components_):
        top_indices = topic.argsort()[-15:][::-1]
        top_terms = [feature_names[i] for i in top_indices]
        print(f"Topic {topic_idx + 1}:")
        print(f"  {', '.join(top_terms)}\n")


def analyze_categories(questions: List[Dict[str, Any]]):
    """Analyze category distributions."""
    print(f"\n{'='*80}")
    print("CATEGORY ANALYSIS")
    print(f"{'='*80}\n")

    primary_categories = Counter()
    secondary_categories = Counter()
    category_pairs = Counter()

    for q in questions:
        category = q.get("category", {})
        primary = category.get("primary")
        secondary = category.get("secondary") or []
        if isinstance(secondary, str):
            secondary = [secondary]

        if primary:
            primary_categories[primary] += 1

            for sec in secondary:
                secondary_categories[sec] += 1
                category_pairs[(primary, sec)] += 1

    print("PRIMARY CATEGORIES:")
    for category, count in primary_categories.most_common():
        percentage = (count / len(questions)) * 100
        print(f"  {category:.<30} {count:>4} ({percentage:.1f}%)")

    print("\n\nSECONDARY CATEGORIES:")
    for category, count in secondary_categories.most_common():
        normalized_category = category or "None"
        percentage = (count / len(questions)) * 100
        print(f"  {normalized_category:.<30} {count:>4} ({percentage:.1f}%)")

    print(f"\n\nTOP 20 SECONDARY CATEGORIES:")
    for category, count in secondary_categories.most_common(20):
        print(f"  {category:.<30} {count:>4}")

    print(f"\n\nTOP 20 CATEGORY COMBINATIONS (Primary + Secondary):")
    for (primary, secondary), count in category_pairs.most_common(20):
        primary_secondary = f"{primary} → {secondary}"
        print(f"  {primary_secondary:.<35} {count:>4}")


def analyze_answers(questions: List[Dict[str, Any]]):
    """Analyze answer patterns."""
    print(f"\n{'='*80}")
    print("ANSWER ANALYSIS")
    print(f"{'='*80}\n")

    answers = extract_answers(questions)
    answer_counts = Counter(answers)

    print(f"Total unique answers: {len(answer_counts)}")
    print(f"Total answers: {len(answers)}")

    print(f"\n\nTOP 50 MOST COMMON ANSWERS:")
    for answer, count in answer_counts.most_common(50):
        print(f"  {count:>3}x  {answer}")

    # Analyze answer lengths
    answer_lengths = [len(ans.split()) for ans in answers if ans]
    print(f"\n\nANSWER LENGTH STATISTICS:")
    print(f"  Mean length: {np.mean(answer_lengths):.1f} words")
    print(f"  Median length: {np.median(answer_lengths):.1f} words")
    print(f"  Min length: {np.min(answer_lengths)} words")
    print(f"  Max length: {np.max(answer_lengths)} words")


def analyze_answers_by_category(questions: List[Dict[str, Any]]):
    """Analyze common answers within each category."""
    print(f"\n{'='*80}")
    print("COMMON ANSWERS BY CATEGORY")
    print(f"{'='*80}\n")

    category_answers = defaultdict(list)

    for q in questions:
        primary = q.get("category", {}).get("primary")
        if not primary:
            continue

        if q.get("type") == "starter" and q.get("correct_answer"):
            category_answers[primary].append(q["correct_answer"])
        elif q.get("type") == "bonus":
            for part in q.get("parts", []):
                if part.get("correct_answer"):
                    category_answers[primary].append(part["correct_answer"])

    for category in sorted(category_answers.keys()):
        answers = category_answers[category]
        answer_counts = Counter(answers)

        print(f"\n{category} (top 10 answers):")
        for answer, count in answer_counts.most_common(10):
            print(f"  {count:>3}x  {answer}")


def analyze_question_modes(questions: List[Dict[str, Any]]):
    """Analyze question mode distributions."""
    print(f"\n{'='*80}")
    print("QUESTION MODE ANALYSIS")
    print(f"{'='*80}\n")

    mode_counts = Counter()
    mode_by_category = defaultdict(Counter)

    for q in questions:
        mode = q.get("question_mode")
        primary = q.get("category", {}).get("primary")

        if mode:
            mode_counts[mode] += 1
            if primary:
                mode_by_category[primary][mode] += 1

    print("OVERALL QUESTION MODES:")
    for mode, count in mode_counts.most_common():
        percentage = (count / len(questions)) * 100
        print(f"  {mode:.<20} {count:>4} ({percentage:.1f}%)")

    print(f"\n\nQUESTION MODES BY CATEGORY:")
    for category in sorted(mode_by_category.keys()):
        print(f"\n{category}:")
        total = sum(mode_by_category[category].values())
        for mode, count in mode_by_category[category].most_common():
            percentage = (count / total) * 100
            print(f"  {mode:.<20} {count:>4} ({percentage:.1f}%)")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze topics and patterns in University Challenge transcripts"
    )
    parser.add_argument(
        "--data-path",
        default="./data/questions/gpt-5-mini",
        help="Path to parsed question data (default: ./data/questions/gpt-5-mini)"
    )
    parser.add_argument(
        "--n-topics",
        type=int,
        default=15,
        help="Number of topics for topic modeling (default: 15)"
    )
    parser.add_argument(
        "--method",
        choices=["lda", "nmf"],
        default="lda",
        help="Topic modeling method (default: lda)"
    )
    parser.add_argument(
        "--skip-topic-modeling",
        action="store_true",
        help="Skip topic modeling (only show basic analytics)"
    )

    args = parser.parse_args()

    # Load data
    questions = load_all_questions(args.data_path)

    if not questions:
        print("No questions found!")
        return

    # Basic analytics
    analyze_categories(questions)
    analyze_question_modes(questions)
    analyze_answers(questions)
    analyze_answers_by_category(questions)

    # Topic modeling on question text
    if not args.skip_topic_modeling:
        texts = extract_question_texts(questions)
        print(f"\nExtracted {len(texts)} question texts for topic modeling")

        if texts:
            perform_topic_modeling(texts, n_topics=args.n_topics, method=args.method)

    print(f"\n{'='*80}")
    print("Analysis complete!")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
