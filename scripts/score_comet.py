"""Score the released translation workbooks with COMET.

This stage is implemented. It uses ``Unbabel/wmt22-comet-da``, the COMET
checkpoint named in the paper, via ``unbabel-comet``.

Inputs
------
``translations/translations_{de2en|ru2en}_{news|idioms}.xlsx``

Each sheet has 250 rows. ``Original_text`` is the source and
``Gold_translation`` is the reference. Every other non-empty column is a
system hypothesis, except ``Idiom`` (the idiom span, not a translation).
Idiom workbooks also contain ``Gold_Idiom``, the reference idiom phrase.
``translations_ru2en_news.xlsx`` has a blank column header between
``M4T_transcription+translation`` and ``Llama``; that column is skipped.

The released COMET workbooks do not score ``Deepseek``, ``M4T+Deepseek``,
or ``Whisper+Deepseek``. Pass ``--layout released`` to score the same
system set as those workbooks, including ``Gold_Idiom`` on idiom files.
In that layout the segment columns follow the released order:
``Gold_Idiom_score`` / ``Gold_Idiom`` come right after ``Idiom``.
The default ``--layout all`` scores every hypothesis column, so DeepSeek
is included. System rows are sorted by COMET score, high to low, which
is how the released system workbooks are ordered.

Outputs
-------
Segment workbook, one row per source sentence:

- ``Original_text``, ``Gold_translation``
- idiom files also keep ``Idiom``
- then ``{system}_score``, ``{system}`` for each scored system
- ``Gold_Idiom`` is written as ``Gold_Idiom_score``, ``Gold_Idiom`` when
  it is included

System workbook, columns ``System``, ``COMET Score``, ``Std Dev``.
``COMET Score`` is the mean of the segment scores. ``Std Dev`` is the
population standard deviation (``ddof=0``). That is the definition that
reproduces the released ``*_system_scores.xlsx`` files from the released
segment scores. Check it without downloading the model:

    python scripts/score_comet.py --verify-released

Empty hypotheses are omitted from the mean and standard deviation and
stored as missing scores. The script writes under ``comet_scores/rescored/``
unless ``--output-dir`` is set, and will not overwrite a released workbook
unless ``--overwrite`` is passed.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.data_layout import (  # noqa: E402
    DOMAINS,
    METADATA_COLUMNS,
    MODEL_IDS,
    PAIRS,
    RELEASED_SYSTEMS,
    ROOT,
    segment_score_path,
    system_score_path,
    translation_path,
)


def _import_pandas():
    try:
        import pandas as pd
    except ImportError as exc:
        raise SystemExit(
            "pandas and openpyxl are required. pip install -r requirements.txt"
        ) from exc
    return pd


def _is_blank_header(name: object) -> bool:
    text = "" if name is None else str(name)
    return text.strip() == "" or text.startswith("Unnamed") or text == "nan"


def hypothesis_columns(frame, layout: str) -> list[str]:
    """System columns to score, in workbook order, for one translation sheet."""
    columns: list[str] = []
    for name in frame.columns:
        text = str(name)
        if text in METADATA_COLUMNS or _is_blank_header(text):
            continue
        if layout == "released" and text not in RELEASED_SYSTEMS:
            continue
        columns.append(text)
    # Released segment workbooks place Gold_Idiom immediately after Idiom,
    # before the system columns. It is a reference phrase, not a system.
    if layout == "released" and "Gold_Idiom" in frame.columns:
        columns.insert(0, "Gold_Idiom")
    return columns


def _segment_systems(frame) -> list[tuple[str, str]]:
    """Return (system name, score column) pairs from a segment-score sheet."""
    columns = list(frame.columns)
    found: list[tuple[str, str]] = []
    index = 0
    while index < len(columns):
        column = str(columns[index])
        if column.endswith("_score") and index + 1 < len(columns):
            system = column[: -len("_score")]
            if str(columns[index + 1]) == system:
                found.append((system, column))
                index += 2
                continue
        index += 1
    return found


def population_std(values: list[float]) -> float:
    """Population standard deviation, matching the released system workbooks."""
    import numpy as np

    array = np.asarray(values, dtype=float)
    if array.size == 0:
        return float("nan")
    return float(np.std(array, ddof=0))


def aggregate_system_scores(frame) -> list[tuple[str, float, float]]:
    """Mean and population std of each ``*_score`` column, in sheet order."""
    rows: list[tuple[str, float, float]] = []
    for system, score_column in _segment_systems(frame):
        series = frame[score_column]
        values = [float(value) for value in series.tolist() if _is_number(value)]
        if not values:
            continue
        mean = sum(values) / len(values)
        rows.append((system, mean, population_std(values)))
    return rows


def _is_number(value: object) -> bool:
    if value is None:
        return False
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return not math.isnan(number)


def verify_released(scores_dir: Path) -> int:
    """Recompute system means from segment workbooks and compare."""
    pd = _import_pandas()
    mismatches = 0
    checked = 0
    for pair in PAIRS:
        for domain in DOMAINS:
            segment_path = scores_dir / segment_score_path(pair, domain).name
            system_path = scores_dir / system_score_path(pair, domain).name
            segments = pd.read_excel(segment_path, engine="openpyxl")
            systems = pd.read_excel(system_path, engine="openpyxl")
            recomputed = {name: (mean, std) for name, mean, std in aggregate_system_scores(segments)}
            released: dict[str, tuple[float, float]] = {}
            for _, row in systems.iterrows():
                name = str(row["System"])
                released[name] = (float(row["COMET Score"]), float(row["Std Dev"]))
            names = sorted(set(recomputed) | set(released))
            print(f"{segment_path.name}: {len(recomputed)} systems")
            for name in names:
                checked += 1
                if name not in recomputed or name not in released:
                    side = "segment" if name not in released else "system"
                    print(f"  MISSING from {side} file: {name}")
                    mismatches += 1
                    continue
                got_mean, got_std = recomputed[name]
                exp_mean, exp_std = released[name]
                if not (
                    math.isclose(got_mean, exp_mean, rel_tol=0.0, abs_tol=1e-9)
                    and math.isclose(got_std, exp_std, rel_tol=0.0, abs_tol=1e-9)
                ):
                    print(
                        f"  MISMATCH {name}: recomputed mean={got_mean:.12f} "
                        f"std={got_std:.12f}; released mean={exp_mean:.12f} "
                        f"std={exp_std:.12f}"
                    )
                    mismatches += 1
    if mismatches:
        print(f"FAILED: {mismatches} system rows out of {checked} did not match.")
        return 1
    print(
        f"OK: {checked} system rows match the released workbooks "
        "(mean and population std, ddof=0)."
    )
    return 0


def dry_run(layout: str) -> None:
    pd = _import_pandas()
    for pair in PAIRS:
        for domain in DOMAINS:
            path = translation_path(pair, domain)
            frame = pd.read_excel(path, engine="openpyxl")
            columns = hypothesis_columns(frame, layout)
            blanks = [str(name) for name in frame.columns if _is_blank_header(name)]
            print(
                f"{path.name}: {len(frame)} rows, layout={layout}, "
                f"{len(columns)} hypothesis columns"
            )
            print("  " + ", ".join(columns))
            if blanks:
                print(f"  skipped blank headers: {blanks}")


def _cell_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    return str(value)


def _load_comet(model_name: str):
    try:
        from comet import download_model, load_from_checkpoint
    except ImportError as exc:
        raise SystemExit(
            "unbabel-comet is not installed. pip install -r requirements.txt"
        ) from exc
    checkpoint = download_model(model_name)
    return load_from_checkpoint(checkpoint)


def _predict(model, samples: list[dict[str, str]], batch_size: int, gpus: int) -> list[float]:
    import inspect

    if not samples:
        return []
    signature = inspect.signature(model.predict)
    kwargs: dict[str, object] = {
        "batch_size": batch_size,
        "gpus": max(gpus, 0),
        "progress_bar": True,
    }
    if "accelerator" in signature.parameters:
        kwargs["accelerator"] = "cpu" if gpus <= 0 else "gpu"
    if "num_workers" in signature.parameters:
        kwargs["num_workers"] = 0
    prediction = model.predict(samples, **kwargs)
    if hasattr(prediction, "scores"):
        return [float(score) for score in prediction.scores]
    if isinstance(prediction, (list, tuple)) and prediction:
        return [float(score) for score in prediction[0]]
    raise TypeError(f"Unrecognized COMET prediction type: {type(prediction)!r}")


def score_workbook(
    frame,
    columns: list[str],
    model,
    batch_size: int,
    gpus: int,
    max_segments: int | None,
):
    """Return a segment dataframe and system rows for one workbook."""
    pd = _import_pandas()
    if max_segments is not None:
        frame = frame.iloc[:max_segments].copy()
    sources = [_cell_text(value) for value in frame["Original_text"].tolist()]
    references = [_cell_text(value) for value in frame["Gold_translation"].tolist()]
    output = pd.DataFrame({"Original_text": sources, "Gold_translation": references})
    if "Idiom" in frame.columns:
        output.insert(2, "Idiom", [_cell_text(value) for value in frame["Idiom"].tolist()])

    system_rows: list[tuple[str, float, float]] = []
    for system in columns:
        hypotheses = [_cell_text(value) for value in frame[system].tolist()]
        samples = []
        sample_indexes: list[int] = []
        for index, (source, hypothesis, reference) in enumerate(
            zip(sources, hypotheses, references)
        ):
            if source and hypothesis and reference:
                samples.append({"src": source, "mt": hypothesis, "ref": reference})
                sample_indexes.append(index)
        print(f"  {system}: scoring {len(samples)} / {len(frame)} segments")
        predicted = _predict(model, samples, batch_size, gpus)
        if len(predicted) != len(sample_indexes):
            raise SystemExit(
                f"COMET returned {len(predicted)} scores for {len(sample_indexes)} "
                f"{system} segments."
            )
        scores: list[float] = [float("nan")] * len(frame)
        for index, score in zip(sample_indexes, predicted):
            scores[index] = score
        # Gold_Idiom keeps the released column order: score, then the phrase.
        output[f"{system}_score"] = scores
        output[system] = hypotheses
        kept = [score for score in scores if _is_number(score)]
        if kept:
            system_rows.append((system, sum(kept) / len(kept), population_std(kept)))
    system_frame = pd.DataFrame(system_rows, columns=["System", "COMET Score", "Std Dev"])
    # The released system workbooks are ordered by COMET score, high to low.
    if not system_frame.empty:
        system_frame = system_frame.sort_values(
            "COMET Score", ascending=False, kind="mergesort"
        ).reset_index(drop=True)
    return output, system_frame


def write_scores(layout: str, output_dir: Path, overwrite: bool, args: argparse.Namespace) -> None:
    pairs = _selected(args.pairs, PAIRS)
    domains = _selected(args.domains, DOMAINS)
    pd = _import_pandas()
    output_dir.mkdir(parents=True, exist_ok=True)
    model = _load_comet(args.model)
    for pair in pairs:
        for domain in domains:
            source = translation_path(pair, domain)
            frame = pd.read_excel(source, engine="openpyxl")
            columns = hypothesis_columns(frame, layout)
            if args.systems:
                requested = [item.strip() for item in args.systems.split(",") if item.strip()]
                missing = [item for item in requested if item not in columns]
                if missing:
                    raise SystemExit(
                        f"{source.name} has no hypothesis column(s) {missing} "
                        f"under layout={layout}."
                    )
                columns = requested
            print(f"{source.name}: {len(columns)} systems")
            segments, systems = score_workbook(
                frame,
                columns,
                model,
                batch_size=args.batch_size,
                gpus=args.gpus,
                max_segments=args.max_segments,
            )
            segment_out = output_dir / f"{pair}_{domain}_segment_scores.xlsx"
            system_out = output_dir / f"{pair}_{domain}_system_scores.xlsx"
            for path in (segment_out, system_out):
                released = path.parent == (ROOT / "comet_scores") and path.exists()
                if released and not overwrite:
                    raise SystemExit(
                        f"Refusing to overwrite released file {path}. "
                        "Pass --overwrite or write to another --output-dir."
                    )
            segments.to_excel(segment_out, index=False)
            systems.to_excel(system_out, index=False)
            print(f"  wrote {segment_out}")
            print(f"  wrote {system_out}")


def _selected(raw: str | None, allowed: tuple[str, ...]) -> tuple[str, ...]:
    if not raw:
        return allowed
    chosen = tuple(item.strip() for item in raw.split(",") if item.strip())
    unknown = [item for item in chosen if item not in allowed]
    if unknown:
        raise SystemExit(f"Unknown value(s) {unknown}. Choose from {allowed}.")
    return chosen


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Score translations/*.xlsx with COMET, or check that the released "
            "system scores are the mean and population std of the segment scores."
        )
    )
    parser.add_argument(
        "--verify-released",
        action="store_true",
        help="Recompute system scores from comet_scores/*_segment_scores.xlsx and compare.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List hypothesis columns in the translation workbooks and exit.",
    )
    parser.add_argument(
        "--layout",
        choices=("all", "released"),
        default="all",
        help=(
            "all scores every hypothesis column, including DeepSeek. "
            "released scores the columns present in comet_scores/."
        ),
    )
    parser.add_argument("--model", default=MODEL_IDS["comet"])
    parser.add_argument("--output-dir", type=Path, default=ROOT / "comet_scores" / "rescored")
    parser.add_argument("--scores-dir", type=Path, default=ROOT / "comet_scores")
    parser.add_argument("--pairs", help="Comma-separated subset of de2en,ru2en.")
    parser.add_argument("--domains", help="Comma-separated subset of news,idioms.")
    parser.add_argument("--systems", help="Comma-separated hypothesis columns to score.")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument(
        "--gpus",
        type=int,
        default=0,
        help="GPU count passed to COMET. 0 scores on CPU. Default: 0.",
    )
    parser.add_argument(
        "--max-segments",
        type=int,
        default=None,
        help="Score only the first N rows of each workbook. For a smoke test.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow writing on top of the released files in comet_scores/.",
    )
    args = parser.parse_args(argv)
    if args.max_segments is not None and args.max_segments < 1:
        parser.error("--max-segments must be >= 1")
    return args


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.verify_released:
        raise SystemExit(verify_released(args.scores_dir))
    if args.dry_run:
        dry_run(args.layout)
        return
    write_scores(args.layout, args.output_dir, args.overwrite, args)


if __name__ == "__main__":
    main()
