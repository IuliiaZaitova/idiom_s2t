"""DecoderLens layer-wise translations for encoder-decoder models.

This file is a placeholder. The original DecoderLens hooks (Langedijk et
al., 2024) were not in the public snapshot. ``--check-existing`` reports
what the released TSVs contain and does not load a model.

What the paper did
------------------
DecoderLens swaps the final encoder output for an intermediate encoder
layer and decodes that state to text. The paper ran it for Whisper,
SeamlessM4T speech-to-text, SeamlessM4T text-to-text, and NLLB, on 50
examples per condition, then annotated those outputs. Annotation labels
are not included in this repository.

Released files
--------------
``decoderlens/translations_dede_idioms_nllb_decoderlens.tsv``

- Intended columns: ``Line Number``, ``Encoder Layer``, ``Translation``.
- 250 German idiom sentences, encoder layer index 0 through 24
  (6,250 logical rows, 12,476 physical lines including the header).
- 249 sentences are not strict TSV. The source was written with a leading
  quote and a newline before the closing quote, so a sentence such as
  ``Es ist mir wurst, wenn du nicht kommst.`` occupies one physical line
  and the layer and translation occupy the next line (``"\\t0\\t...``).
- The last sentence (``Mach doch nicht so einen krummen Rücken...``) is
  25 ordinary TSV rows, source and layer on the same line.

``decoderlens/translations_dede_idioms_m4t_text_decoderlens.tsv``

- Header: ``Source Text (RU)``, ``Layer Index``, ``Translation (Lens)``.
  The header says RU. The source text in the file is German.
- One German sentence, layers 0-24, with some layers repeated. This is a
  partial dump, not the 50-example annotation set.

``decoderlens/translations_dede_idioms_m4t_text_decoderlens_ewae.tsv``

- Same header. One Russian sentence (``Однако полиция не захотела...``),
  layers 0-24, one row per layer. The filename says ``dede``.

An implementation pasted at the TODO should write strict TSV with one
row per (source, layer) and should not reuse the split-quote layout.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.data_layout import MODEL_IDS, decoderlens_paths  # noqa: E402

# 249 sentences were written as a quoted source line, then a line that
# starts with the closing quote, a tab, the layer, and the translation.
_QUOTED_LAYER_LINE = re.compile(r'^"\t(\d+)\t', re.MULTILINE)
# One sentence is ordinary TSV: source, layer, translation on one line.
_PLAIN_LAYER_LINE = re.compile(r"^[^\t\"].*\t(\d+)\t")


def _check_nllb(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    problems: list[str] = []
    if not lines or lines[0] != "Line Number\tEncoder Layer\tTranslation":
        problems.append(f"{path.name} is missing the expected header")
        return problems
    quoted = [int(match.group(1)) for match in _QUOTED_LAYER_LINE.finditer(text)]
    plain = []
    for line in lines[1:]:
        match = _PLAIN_LAYER_LINE.match(line)
        if match:
            plain.append(int(match.group(1)))
    layers = quoted + plain
    print(
        f"{path.name}: {len(lines)} physical lines, "
        f"{len(quoted)} quote-split records, {len(plain)} single-line records, "
        f"layer ids {min(layers) if layers else 'n/a'}-{max(layers) if layers else 'n/a'}."
    )
    if len(layers) != 6250:
        problems.append(
            f"{path.name} has {len(layers)} layer records, expected 6250 "
            "(250 sentences x layers 0-24)"
        )
    if layers and (min(layers) != 0 or max(layers) != 24):
        problems.append(f"{path.name} layer span is {min(layers)}-{max(layers)}, expected 0-24")
    if sum(layer == 0 for layer in layers) != 250:
        problems.append(f"{path.name} does not have 250 records at layer 0")
    print(
        "  249 sentences are split across a newline inside quotes. "
        "One sentence is stored as ordinary TSV rows."
    )
    return problems


def _check_m4t(path: Path) -> list[str]:
    problems: list[str] = []
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle, delimiter="\t"))
    if not rows:
        return [f"{path.name} is empty"]
    header = rows[0]
    expected = ["Source Text (RU)", "Layer Index", "Translation (Lens)"]
    if header != expected:
        problems.append(f"{path.name} header is {header}, expected {expected}")
        return problems
    sources = {row[0] for row in rows[1:] if len(row) >= 2}
    layers = [int(row[1]) for row in rows[1:] if len(row) >= 2 and row[1].isdigit()]
    print(
        f"{path.name}: {len(rows) - 1} data rows, "
        f"{len(sources)} distinct source sentence(s), "
        f"layers {min(layers) if layers else 'n/a'}-{max(layers) if layers else 'n/a'}."
    )
    if not layers or min(layers) != 0 or max(layers) != 24:
        problems.append(f"{path.name} does not cover layers 0-24")
    return problems


def check_existing() -> None:
    paths = decoderlens_paths()
    problems = _check_nllb(paths["nllb"])
    problems.extend(_check_m4t(paths["m4t_text"]))
    problems.extend(_check_m4t(paths["m4t_text_ewae"]))
    if problems:
        print("DecoderLens files do not match the expected layout:")
        for item in problems:
            print(f"  - {item}")
        raise SystemExit(1)
    print("OK: released DecoderLens TSVs match the counts described in the docstring.")


def run_decoderlens(_args: argparse.Namespace) -> None:
    # TODO(author): paste original implementation
    raise SystemExit(
        "DecoderLens analysis is not included in this release. Paste the "
        "original implementation at the TODO marker in "
        "scripts/decoderlens_analysis.py. Write strict TSV; do not reuse "
        "the split-quote layout of the released NLLB file."
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Decode intermediate encoder layers with DecoderLens. "
            "Placeholder: the analysis itself is not included."
        )
    )
    parser.add_argument(
        "--model",
        choices=("whisper", "seamless-speech", "seamless-text", "nllb"),
    )
    parser.add_argument("--language", choices=("de", "ru"))
    parser.add_argument("--domain", choices=("news", "idioms"))
    parser.add_argument(
        "--max-examples",
        type=int,
        default=50,
        help="The paper annotated 50 examples per condition. Default: 50.",
    )
    parser.add_argument("--model-id", help="Override the model named in the paper.")
    parser.add_argument("--device", default="cuda")
    parser.add_argument(
        "--output",
        type=Path,
        help="Strict TSV to write: source, layer, translation.",
    )
    parser.add_argument(
        "--check-existing",
        action="store_true",
        help="Inspect decoderlens/*.tsv and exit. Does not load a model.",
    )
    args = parser.parse_args(argv)
    if not args.check_existing:
        missing = [
            name for name in ("model", "language", "domain") if getattr(args, name) is None
        ]
        if missing:
            parser.error(
                "analysis requires "
                + ", ".join("--" + name for name in missing)
                + " (or pass --check-existing)"
            )
    return args


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.check_existing:
        check_existing()
        return
    if args.model == "seamless-speech" or args.model == "seamless-text":
        default_id = MODEL_IDS["seamless"]
    else:
        default_id = MODEL_IDS[args.model]
    args.model_id = args.model_id or default_id
    print(
        f"Resolved DecoderLens for {args.model_id} on {args.language} "
        f"{args.domain}, up to {args.max_examples} examples."
    )
    run_decoderlens(args)


if __name__ == "__main__":
    main()
