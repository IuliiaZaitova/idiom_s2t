"""Redraw the COMET summary figures from the released system-score workbooks.

This stage is implemented. It reads ``comet_scores/*_system_scores.xlsx``
and writes:

- ``de_performance_comparison.png`` and ``ru_performance_comparison.png``:
  idiom COMET (x) against news COMET (y), one marker per system. This is
  the same comparison as the PNGs already in ``plots/``.
- ``comet_news_vs_idioms.png``: grouped bars of news vs. idiom COMET for
  the systems that the score files actually contain.

``plots/slt_vs_mt_idioms_de_en.png`` also draws a literal-translation rate
and includes DeepSeek. Neither of those series is a column in
``comet_scores/`` (DeepSeek hypotheses are in ``translations/`` but were
not scored in the released workbooks; literal-translation counts were not
released). This script does not redraw that figure and does not hard-code
its percentages.

Rows named ``Gold_Idiom`` or ``Unnamed: *`` are omitted. They are not
translation systems.

The default output directory is ``plots/regenerated/``, so the paper PNGs
are left in place.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.data_layout import PAIRS, ROOT, system_score_path  # noqa: E402

# Marker, color, legend label, and legend group. Order is the legend order.
STYLES: list[tuple[str, str, str, str, str]] = [
    ("M4T_text", "s", "#2ca02c", "M4T (Text)", "Text Models"),
    ("NLLB", "s", "#1f77b4", "NLLB", "Text Models"),
    ("Llama", "s", "#e377c2", "LLaMA", "Text Models"),
    ("M4T_audio", "o", "#111111", "M4T (Audio)", "Audio Models"),
    ("Whisper", "o", "#ff7f0e", "Whisper", "Audio Models"),
    ("Whisper_M4T", "D", "#17becf", "Whisper + M4T (Text)", "Combined Models"),
    ("Whisper+NLLB", "D", "#7fcdbb", "Whisper + NLLB", "Combined Models"),
    (
        "M4T_transcription+translation",
        "D",
        "#2ca02c",
        "M4T (Transcription + Translation)",
        "Combined Models",
    ),
    ("Whisper_Llama", "D", "#ff7f0e", "Whisper + LLaMA", "Combined Models"),
    ("M4T_NLLB", "D", "#1f77b4", "M4T (Audio) + NLLB", "Combined Models"),
    ("M4T_Llama", "D", "#7b2d8e", "M4T (Audio) + LLaMA", "Combined Models"),
]

BAR_SYSTEMS = [
    ("Whisper", "Whisper (SLT)"),
    ("M4T_audio", "SeamlessM4T (SLT)"),
    ("Llama", "LLaMA"),
    ("M4T_text", "SeamlessM4T (MT)"),
    ("NLLB", "NLLB (MT)"),
]

PAIR_TITLES = {
    "de2en": "German → English",
    "ru2en": "Russian → English",
}


def _import_stack():
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import pandas as pd
    except ImportError as exc:
        raise SystemExit(
            "pandas, openpyxl, and matplotlib are required. "
            "pip install -r requirements.txt"
        ) from exc
    return pd, plt


def _ignored(name: str) -> bool:
    return name == "Gold_Idiom" or name.startswith("Unnamed") or name.strip() in {"", "nan"}


def load_system_means(path: Path) -> dict[str, float]:
    pd, _plt = _import_stack()
    frame = pd.read_excel(path, engine="openpyxl")
    if list(frame.columns[:3]) != ["System", "COMET Score", "Std Dev"]:
        raise SystemExit(f"{path} does not have columns System, COMET Score, Std Dev.")
    scores: dict[str, float] = {}
    for _, row in frame.iterrows():
        name = str(row["System"])
        if _ignored(name):
            continue
        scores[name] = float(row["COMET Score"])
    return scores


def _style_for(system: str) -> tuple[str, str, str, str]:
    for name, marker, color, label, group in STYLES:
        if name == system:
            return marker, color, label, group
    return "o", "#7f7f7f", system, "Other"


def _ordered_systems(available: set[str]) -> list[str]:
    known = [name for name, *_rest in STYLES if name in available]
    extra = sorted(available - {name for name, *_rest in STYLES})
    return known + extra


def plot_scatter(pair: str, news: dict[str, float], idioms: dict[str, float], output: Path, plt) -> None:
    from matplotlib.lines import Line2D

    shared = _ordered_systems(set(news) & set(idioms))
    if len(shared) < 8:
        raise SystemExit(
            f"{pair} has only {len(shared)} systems in both news and idiom scores."
        )
    only_news = sorted(set(news) - set(idioms))
    only_idioms = sorted(set(idioms) - set(news))
    if only_news or only_idioms:
        print(
            f"Note: {pair} systems not in both domains are omitted "
            f"(news only {only_news}, idioms only {only_idioms})."
        )

    fig, ax = plt.subplots(figsize=(8.6, 6.5))
    ax.set_facecolor("#f3f1f7")
    values = [news[name] for name in shared] + [idioms[name] for name in shared]
    low = min(values) - 0.025
    high = max(values) + 0.025
    ax.plot([low, high], [low, high], linestyle=(0, (1, 2)), color="#b0b0b0", linewidth=1, zorder=0)

    handles: list[Line2D] = []
    labels: list[str] = []
    seen_groups: list[str] = []
    for system in shared:
        marker, color, label, group = _style_for(system)
        ax.scatter(
            idioms[system],
            news[system],
            marker=marker,
            c=color,
            s=70,
            zorder=3,
            edgecolors="white",
            linewidths=0.4,
        )
        if group not in seen_groups:
            seen_groups.append(group)
            handles.append(Line2D([], [], linestyle="None"))
            labels.append(group + ":")
        handles.append(
            Line2D(
                [],
                [],
                color=color,
                marker=marker,
                linestyle="None",
                markersize=7,
                markeredgewidth=0,
            )
        )
        labels.append(label)

    ax.set_xlim(low, high)
    ax.set_ylim(low, high)
    ax.set_xlabel("COMET Score (Idioms)")
    ax.set_ylabel("COMET Score (News)")
    ax.set_title(f"System Performance: Idioms vs. News\n{PAIR_TITLES[pair]}")
    ax.grid(True, color="white", linewidth=1.0)
    ax.set_axisbelow(True)
    ax.legend(handles, labels, loc="lower right", frameon=True, fontsize=8, borderpad=0.8)
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)
    print(f"Wrote {output} ({len(shared)} systems).")


def plot_bars(by_pair: dict[str, tuple[dict[str, float], dict[str, float]]], output: Path, plt) -> None:
    import numpy as np

    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.8), sharey=True)
    width = 0.38
    for axis, pair in zip(axes, PAIRS):
        news, idioms = by_pair[pair]
        present = [(key, label) for key, label in BAR_SYSTEMS if key in news and key in idioms]
        if len(present) != len(BAR_SYSTEMS):
            missing = [key for key, _label in BAR_SYSTEMS if key not in news or key not in idioms]
            raise SystemExit(f"{pair} is missing bar-chart systems {missing}.")
        positions = np.arange(len(present))
        news_values = [news[key] for key, _label in present]
        idiom_values = [idioms[key] for key, _label in present]
        axis.bar(positions - width / 2, news_values, width, label="News", color="#4C78A8")
        axis.bar(positions + width / 2, idiom_values, width, label="Idioms", color="#F58518")
        axis.set_xticks(positions)
        axis.set_xticklabels([label for _key, label in present], rotation=25, ha="right")
        axis.set_title(PAIR_TITLES[pair])
        axis.set_ylim(0.0, 1.0)
        axis.grid(True, axis="y", color="#e6e6e6", linewidth=0.8)
        axis.set_axisbelow(True)
    axes[0].set_ylabel("COMET Score")
    axes[0].legend(frameon=False, loc="upper right")
    fig.suptitle("COMET on news and idioms")
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)
    print(f"Wrote {output}.")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Regenerate COMET summary plots from comet_scores/*_system_scores.xlsx."
    )
    parser.add_argument("--scores-dir", type=Path, default=ROOT / "comet_scores")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "plots" / "regenerated")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    _pd, plt = _import_stack()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    by_pair: dict[str, tuple[dict[str, float], dict[str, float]]] = {}
    filenames = {
        "de2en": "de_performance_comparison.png",
        "ru2en": "ru_performance_comparison.png",
    }
    for pair in PAIRS:
        news = load_system_means(args.scores_dir / system_score_path(pair, "news").name)
        idioms = load_system_means(args.scores_dir / system_score_path(pair, "idioms").name)
        by_pair[pair] = (news, idioms)
        plot_scatter(pair, news, idioms, args.output_dir / filenames[pair], plt)
    plot_bars(by_pair, args.output_dir / "comet_news_vs_idioms.png", plt)


if __name__ == "__main__":
    main()
