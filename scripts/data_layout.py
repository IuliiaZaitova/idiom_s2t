"""Paths and column names for the released evaluation artifacts."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

N_EVAL = 250

# Hypothesis columns scored in the released COMET workbooks.
# DeepSeek columns are present in translations/*.xlsx but absent from
# comet_scores/. Gold_Idiom is scored only for the idiom workbooks.
RELEASED_SYSTEMS = [
    "NLLB",
    "M4T_text",
    "M4T_audio",
    "Whisper",
    "Whisper+NLLB",
    "M4T_transcription+translation",
    "Llama",
    "M4T_Llama",
    "M4T_NLLB",
    "Whisper_Llama",
    "Whisper_M4T",
]

# Present in the translation workbooks, not in the released COMET workbooks.
DEEPSEEK_SYSTEMS = ["Deepseek", "M4T+Deepseek", "Whisper+Deepseek"]

METADATA_COLUMNS = ["Original_text", "Idiom", "Gold_translation", "Gold_Idiom"]

# COMET checkpoint named in the paper (Section 3.4.1).
MODEL_IDS = {
    "comet": "Unbabel/wmt22-comet-da",
}

PAIRS = ("de2en", "ru2en")
DOMAINS = ("news", "idioms")


def translation_path(pair: str, domain: str) -> Path:
    return ROOT / "translations" / f"translations_{pair}_{domain}.xlsx"


def segment_score_path(pair: str, domain: str) -> Path:
    return ROOT / "comet_scores" / f"{pair}_{domain}_segment_scores.xlsx"


def system_score_path(pair: str, domain: str) -> Path:
    return ROOT / "comet_scores" / f"{pair}_{domain}_system_scores.xlsx"
