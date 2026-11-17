"""File layout of this release.

The constants here describe the files that are actually in the repository.
Inference scripts should read and write these paths rather than inventing
new names.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

N_EVAL = 250

# Hypothesis columns that the released COMET workbooks actually score.
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

# Identifiers printed in the paper. DeepSeek-V3 is the model name from the
# paper; the paper does not give a Hugging Face repository id for it.
MODEL_IDS = {
    "whisper": "openai/whisper-large-v3",
    "seamless": "facebook/seamless-m4t-v2-large",
    "nllb": "facebook/nllb-200-3.3B",
    "llama_de": "VAGOsolutions/LLaMA-3-SauerkrautLM-8b-Instruct",
    "llama_ru": "IlyaGusev/saiga_LLaMA3_8b",
    "deepseek": "DeepSeek-V3",
    "comet": "Unbabel/wmt22-comet-da",
}

PAIRS = ("de2en", "ru2en")
DOMAINS = ("news", "idioms")


def news_paths(pair: str) -> tuple[Path, Path]:
    """Return (source, reference) for the 250-line News Commentary subset."""
    news = ROOT / "dataset" / "news" / "news_commentary"
    if pair == "de2en":
        return (
            news / "News-Commentary.de-en_250.de",
            news / "News-Commentary.de-en_250.en",
        )
    if pair == "ru2en":
        return (
            news / "News-Commentary.en-ru_250.ru",
            news / "News-Commentary.en-ru_250.en",
        )
    raise KeyError(pair)


def idiom_source_path(pair: str) -> Path:
    """250-line evaluation source. References live in the translation workbook."""
    idioms = ROOT / "dataset" / "idioms"
    if pair == "de2en":
        return idioms / "idioms_in_context-test.dede-enus.dede"
    if pair == "ru2en":
        return idioms / "idioms_in_context-test.ruru-enus.ruru"
    raise KeyError(pair)


def translation_path(pair: str, domain: str) -> Path:
    return ROOT / "translations" / f"translations_{pair}_{domain}.xlsx"


def segment_score_path(pair: str, domain: str) -> Path:
    return ROOT / "comet_scores" / f"{pair}_{domain}_segment_scores.xlsx"


def system_score_path(pair: str, domain: str) -> Path:
    return ROOT / "comet_scores" / f"{pair}_{domain}_system_scores.xlsx"


def transcription_path(pair: str, domain: str, asr: str) -> Path:
    """ASR transcript TSV. ``asr`` is ``whisper`` or ``seamless``."""
    code = "dede" if pair == "de2en" else "ruru"
    tag = "whisper" if asr == "whisper" else "m4t_audio"
    name = f"transcriptions_{code}_{domain}_{tag}.tsv"
    return ROOT / "transcriptions" / name


def audio_basename(pair: str, domain: str, index: int) -> str:
    """Filename stored in the ``Audio File`` column. Audio itself is not shipped."""
    if pair == "de2en" and domain == "news":
        stem = f"dede_{index}"
    elif pair == "de2en" and domain == "idioms":
        stem = f"enus_dede_{index}"
    elif pair == "ru2en" and domain == "news":
        stem = f"ruru_{index}"
    elif pair == "ru2en" and domain == "idioms":
        stem = f"enus_ruru_{index}"
    else:
        raise KeyError((pair, domain))
    return f"{stem}.mp3"


def decoderlens_paths() -> dict[str, Path]:
    folder = ROOT / "decoderlens"
    return {
        "nllb": folder / "translations_dede_idioms_nllb_decoderlens.tsv",
        "m4t_text": folder / "translations_dede_idioms_m4t_text_decoderlens.tsv",
        "m4t_text_ewae": folder
        / "translations_dede_idioms_m4t_text_decoderlens_ewae.tsv",
    }
