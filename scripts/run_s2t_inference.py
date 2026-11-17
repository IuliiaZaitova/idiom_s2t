"""ASR and speech-to-text inference with Whisper and SeamlessM4T.

This file is a placeholder. The original inference code was not in the
public snapshot of the repository. The CLI and the ``--check-existing``
check describe the files that *are* in the repository. They do not run
the models.

Inputs
------
Source text for the 250-item evaluation splits:

- German news: ``dataset/news/news_commentary/News-Commentary.de-en_250.de``
- German idioms: ``dataset/idioms/idioms_in_context-test.dede-enus.dede``
- Russian news: ``dataset/news/news_commentary/News-Commentary.en-ru_250.ru``
- Russian idioms: ``dataset/idioms/idioms_in_context-test.ruru-enus.ruru``

Audio is not in the repository. The paper synthesized 16 kHz speech with
Microsoft Edge neural TTS and fed 16 kHz mono audio to the recognizer.
The released transcript index uses ``.mp3`` filenames:

- German news: ``dede_{i}.mp3``
- German idioms: ``enus_dede_{i}.mp3``
- Russian news: ``ruru_{i}.mp3``
- Russian idioms: ``enus_ruru_{i}.mp3``

with ``i`` in ``0 .. 249``.

Models named in the paper:

- ``openai/whisper-large-v3``
- ``facebook/seamless-m4t-v2-large``

Outputs
-------
ASR transcripts, already released, are TSVs with 250 data rows:

- ``transcriptions/transcriptions_{dede|ruru}_{news|idioms}_whisper.tsv``
- ``transcriptions/transcriptions_{dede|ruru}_{news|idioms}_m4t_audio.tsv``

The header is ``Audio File\\tTranscription``, except the two news
SeamlessM4T files (``transcriptions_{dede|ruru}_news_m4t_audio.tsv``),
whose header is ``Audio File\\tTranslation``. The text in those two
files is still a source-language transcript, not an English translation.
Whisper rows often have a leading space on the transcript.
Direct speech-to-text hypotheses are not stored in these TSVs. They are
the ``Whisper`` and ``M4T_audio`` columns of
``translations/translations_{de2en|ru2en}_{news|idioms}.xlsx``, one
hypothesis per row, aligned with ``Original_text``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.data_layout import (  # noqa: E402
    MODEL_IDS,
    N_EVAL,
    PAIRS,
    DOMAINS,
    audio_basename,
    idiom_source_path,
    news_paths,
    transcription_path,
)


def _source_path(pair: str, domain: str) -> Path:
    if domain == "news":
        return news_paths(pair)[0]
    return idiom_source_path(pair)


def check_existing() -> None:
    """Confirm the released transcript TSVs match the layout above."""
    problems: list[str] = []
    for pair in PAIRS:
        for domain in DOMAINS:
            source = _source_path(pair, domain)
            n_source = len(source.read_text(encoding="utf-8").splitlines())
            if n_source != N_EVAL:
                problems.append(f"{source} has {n_source} lines, expected {N_EVAL}")
            for asr in ("whisper", "seamless"):
                path = transcription_path(pair, domain, asr)
                lines = path.read_text(encoding="utf-8").splitlines()
                header = lines[0] if lines else ""
                # News SeamlessM4T files label the transcript column "Translation".
                # The cell text is still a source-language transcript.
                expected_header = (
                    "Audio File\tTranslation"
                    if asr == "seamless" and domain == "news"
                    else "Audio File\tTranscription"
                )
                if header != expected_header:
                    problems.append(
                        f"{path} header is {header!r}, expected {expected_header!r}"
                    )
                    continue
                rows = lines[1:]
                if len(rows) != N_EVAL:
                    problems.append(f"{path} has {len(rows)} rows, expected {N_EVAL}")
                for index, row in enumerate(rows):
                    audio, sep, _text = row.partition("\t")
                    expected = audio_basename(pair, domain, index)
                    if not sep or audio != expected:
                        problems.append(
                            f"{path} row {index} audio is {audio!r}, expected {expected!r}"
                        )
                        break
    if problems:
        print("Released transcript files do not match the expected layout:")
        for item in problems:
            print(f"  - {item}")
        raise SystemExit(1)
    print(
        f"OK: 8 ASR TSVs, each with {N_EVAL} rows, match the released filenames "
        "and the 250-line source files."
    )


def run_inference(_args: argparse.Namespace) -> None:
    # TODO(author): paste original implementation
    raise SystemExit(
        "Whisper / SeamlessM4T inference is not included in this release. "
        "Paste the original implementation at the TODO marker in "
        "scripts/run_s2t_inference.py. --check-existing only validates the "
        "TSVs already in transcriptions/."
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run Whisper or SeamlessM4T ASR / speech-to-text on the "
            "250-sentence evaluation audio. Placeholder: the model call "
            "is not included."
        )
    )
    parser.add_argument(
        "--task",
        choices=("asr", "s2t"),
        help="asr writes a transcript TSV; s2t writes translation hypotheses.",
    )
    parser.add_argument("--model", choices=("whisper", "seamless"))
    parser.add_argument("--language", choices=("de", "ru"))
    parser.add_argument("--domain", choices=DOMAINS)
    parser.add_argument(
        "--audio-dir",
        type=Path,
        help="Directory of synthesized clips. Audio is not part of this repository.",
    )
    parser.add_argument(
        "--model-id",
        help="Override the Hugging Face id. Defaults to the id named in the paper.",
    )
    parser.add_argument("--device", default="cuda")
    parser.add_argument(
        "--output",
        type=Path,
        help="ASR TSV or S2T hypothesis TSV to write. Defaults to the released path for ASR.",
    )
    parser.add_argument(
        "--check-existing",
        action="store_true",
        help="Validate transcriptions/*.tsv and exit. Does not load a model.",
    )
    args = parser.parse_args(argv)
    if not args.check_existing:
        missing = [
            name
            for name in ("task", "model", "language", "domain", "audio_dir")
            if getattr(args, name) is None
        ]
        if missing:
            parser.error(
                "inference requires "
                + ", ".join("--" + name.replace("_", "-") for name in missing)
                + " (or pass --check-existing)"
            )
    return args


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.check_existing:
        check_existing()
        return
    if not args.audio_dir.is_dir():
        raise SystemExit(
            f"Audio directory {args.audio_dir} does not exist. "
            "The synthesized clips are not in this repository."
        )
    pair = "de2en" if args.language == "de" else "ru2en"
    args.model_id = args.model_id or MODEL_IDS[args.model]
    if args.output is None and args.task == "asr":
        args.output = transcription_path(pair, args.domain, args.model)
    print(
        f"Resolved {args.task} with {args.model_id} on {args.language} "
        f"{args.domain} audio in {args.audio_dir}."
    )
    run_inference(args)


if __name__ == "__main__":
    main()
