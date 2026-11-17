"""Text translation with NLLB, SeamlessM4T, LLaMA 3, and DeepSeek-V3.

This file is a placeholder. The original prompting and generation code
was not in the public snapshot. ``--check-existing`` only inspects the
translation workbooks that are already released.

Inputs
------
One source sentence per line, aligned by row with the workbook:

- News, German to English:
  ``dataset/news/news_commentary/News-Commentary.de-en_250.de``
  reference ``News-Commentary.de-en_250.en``
- News, Russian to English:
  ``dataset/news/news_commentary/News-Commentary.en-ru_250.ru``
  reference ``News-Commentary.en-ru_250.en``
- Idioms: the 250-line ``.dede`` / ``.ruru`` files under ``dataset/idioms/``.
  The 1,000-line ``.enus`` files are the upstream Idioms-InContext-MT test
  set and are not line-aligned with this 250-item subset.

Cascaded systems read the ASR TSVs in ``transcriptions/`` instead of the
clean source. The paper kept the transcript's capitalization and punctuation.

Models named in the paper:

- ``facebook/nllb-200-3.3B``
- ``facebook/seamless-m4t-v2-large`` (text-to-text)
- ``VAGOsolutions/LLaMA-3-SauerkrautLM-8b-Instruct`` (German LLaMA 3)
- ``IlyaGusev/saiga_LLaMA3_8b`` (Russian LLaMA 3)
- DeepSeek-V3 (the paper does not give a repository id)

LLaMA and DeepSeek prompts are in Appendix A of the paper. They are not
in this repository.

Outputs
-------
``translations/translations_{de2en|ru2en}_{news|idioms}.xlsx``, 250 data
rows plus a header. Shared columns:

- ``Original_text``, ``Gold_translation``
- idiom files also have ``Idiom`` and ``Gold_Idiom``

Hypothesis columns use the names below. ``+`` and ``_`` are mixed in the
released files; keep those spellings so the columns stay aligned with
``comet_scores/``.

- Text: ``NLLB``, ``M4T_text``, ``Llama``, ``Deepseek``
- Cascaded: ``Whisper+NLLB``, ``Whisper_M4T``, ``Whisper_Llama``,
  ``Whisper+Deepseek``, ``M4T_transcription+translation``, ``M4T_NLLB``,
  ``M4T_Llama``, ``M4T+Deepseek``

``translations_ru2en_news.xlsx`` has an empty column header between
``M4T_transcription+translation`` and ``Llama``. Leave it untouched until
the author confirms what it was.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.data_layout import (  # noqa: E402
    DEEPSEEK_SYSTEMS,
    DOMAINS,
    METADATA_COLUMNS,
    MODEL_IDS,
    N_EVAL,
    PAIRS,
    RELEASED_SYSTEMS,
    translation_path,
)


def check_existing() -> None:
    """Confirm each released workbook has 250 rows and the known columns."""
    try:
        import pandas as pd
    except ImportError as exc:
        raise SystemExit(
            "pandas and openpyxl are required for --check-existing. "
            "pip install -r requirements.txt"
        ) from exc

    expected = set(RELEASED_SYSTEMS) | set(DEEPSEEK_SYSTEMS)
    problems: list[str] = []
    for pair in PAIRS:
        for domain in DOMAINS:
            path = translation_path(pair, domain)
            frame = pd.read_excel(path, engine="openpyxl")
            if len(frame) != N_EVAL:
                problems.append(f"{path.name} has {len(frame)} rows, expected {N_EVAL}")
            for column in ("Original_text", "Gold_translation"):
                if column not in frame.columns:
                    problems.append(f"{path.name} is missing {column}")
            if domain == "idioms":
                for column in ("Idiom", "Gold_Idiom"):
                    if column not in frame.columns:
                        problems.append(f"{path.name} is missing {column}")
            missing = sorted(expected - set(map(str, frame.columns)))
            if missing:
                problems.append(f"{path.name} is missing columns {missing}")
            blank = [str(column) for column in frame.columns if str(column).startswith("Unnamed")]
            if blank:
                print(f"Note: {path.name} has blank header(s) read as {blank}.")
            unknown = [
                str(column)
                for column in frame.columns
                if str(column) not in expected
                and str(column) not in METADATA_COLUMNS
                and not str(column).startswith("Unnamed")
            ]
            if unknown:
                print(f"Note: {path.name} has extra columns {unknown}.")
            print(f"OK {path.name}: {len(frame)} rows, {len(frame.columns)} columns.")
    if problems:
        print("Translation workbooks do not match the expected layout:")
        for item in problems:
            print(f"  - {item}")
        raise SystemExit(1)


def run_translation(_args: argparse.Namespace) -> None:
    # TODO(author): paste original implementation
    raise SystemExit(
        "NLLB, SeamlessM4T text, LLaMA, and DeepSeek generation is not "
        "included in this release. Paste the original implementation, "
        "including the Appendix A prompts, at the TODO marker in "
        "scripts/run_mt.py."
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Translate the 250-sentence news and idiom sets. "
            "Placeholder: generation is not included."
        )
    )
    parser.add_argument(
        "--system",
        choices=(
            "nllb",
            "seamless-text",
            "llama",
            "deepseek",
            "cascade",
        ),
        help="cascade scores an ASR transcript with the MT system in --cascade-mt.",
    )
    parser.add_argument("--language", choices=("de", "ru"))
    parser.add_argument("--domain", choices=DOMAINS)
    parser.add_argument(
        "--cascade-asr",
        choices=("whisper", "seamless"),
        help="Required when --system cascade. Reads transcriptions/*.tsv.",
    )
    parser.add_argument(
        "--cascade-mt",
        choices=("nllb", "seamless-text", "llama", "deepseek"),
        help="Required when --system cascade.",
    )
    parser.add_argument("--model-id", help="Override the model named in the paper.")
    parser.add_argument("--device", default="cuda")
    parser.add_argument(
        "--output",
        type=Path,
        help="Workbook to write. Defaults to translations/translations_{pair}_{domain}.xlsx.",
    )
    parser.add_argument(
        "--check-existing",
        action="store_true",
        help="Validate translations/*.xlsx and exit. Does not load a model.",
    )
    args = parser.parse_args(argv)
    if not args.check_existing:
        missing = [
            name
            for name in ("system", "language", "domain")
            if getattr(args, name) is None
        ]
        if missing:
            parser.error(
                "translation requires "
                + ", ".join("--" + name for name in missing)
                + " (or pass --check-existing)"
            )
        if args.system == "cascade" and (
            args.cascade_asr is None or args.cascade_mt is None
        ):
            parser.error("cascade requires --cascade-asr and --cascade-mt")
    return args


def _default_model_id(args: argparse.Namespace) -> str:
    kind = args.cascade_mt if args.system == "cascade" else args.system
    if kind == "llama":
        return MODEL_IDS["llama_de"] if args.language == "de" else MODEL_IDS["llama_ru"]
    if kind == "seamless-text":
        return MODEL_IDS["seamless"]
    return MODEL_IDS[kind]


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.check_existing:
        check_existing()
        return
    pair = "de2en" if args.language == "de" else "ru2en"
    if args.output is None:
        args.output = translation_path(pair, args.domain)
    args.model_id = args.model_id or _default_model_id(args)
    print(f"Resolved {args.system} ({args.model_id}) for {pair} {args.domain}.")
    print(f"Workbook: {args.output}")
    run_translation(args)


if __name__ == "__main__":
    main()
