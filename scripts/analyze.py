"""Run deterministic retrieval and optional grounded interpretation."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from dataclasses import asdict
from pathlib import Path

from src.analysis import (
    PHASES,
    analyze_with_ollama,
    build_candidates,
    build_deterministic_timeline,
)
from src.corpus import load_book
from src.evidence import retrieve_evidence


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "input"
OUTPUT = ROOT / "data" / "output"


def atomic_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        Path(temporary).unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="write a deterministic timeline without model enrichment",
    )
    parser.add_argument("--model", default="llama3.1:8b", help="local Ollama model")
    args = parser.parse_args()

    try:
        source, chapters = load_book(INPUT)
    except (FileNotFoundError, ValueError) as error:
        print(f"Analysis stopped: {error}")
        return 2

    print(f"Source: {source.name}")
    print(f"Chapters: {len(chapters)}")
    print(f"Words: {sum(len(chapter.text.split()) for chapter in chapters):,}")
    print(f"Range: {chapters[0].heading} — {chapters[-1].heading}")
    candidates = build_candidates(chapters, retrieve_evidence)
    candidate_path = OUTPUT / "candidates.json"
    atomic_json(candidate_path, {
        "note": "Deterministically retrieved candidates; no full pronoun/coreference resolution.",
        "phases": [
            {
                "id": phase["id"],
                "chapter_numbers": phase["chapters"],
                "evidence": [asdict(item) for item in candidates[phase["id"]]],
            }
            for phase in PHASES
        ],
    })
    print(f"Retrieved candidates: {sum(map(len, candidates.values()))}")
    print(f"Candidate evidence: {candidate_path}")

    analysis_path = OUTPUT / "friendship_timeline.json"
    deterministic_timeline = build_deterministic_timeline(candidates)
    if args.no_llm:
        atomic_json(analysis_path, deterministic_timeline)
        print(f"Deterministic timeline: {analysis_path}")
        print("Optional LLM enrichment skipped (--no-llm).")
        return 0
    try:
        analysis = analyze_with_ollama(candidates, model=args.model)
    except (RuntimeError, ValueError) as error:
        print(f"Optional LLM enrichment incomplete: {error}")
        if analysis_path.exists():
            print("Existing friendship_timeline.json was preserved.")
        else:
            atomic_json(analysis_path, deterministic_timeline)
            print(f"Deterministic timeline: {analysis_path}")
        return 0
    atomic_json(analysis_path, analysis)
    print(f"Validated enriched timeline: {analysis_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
