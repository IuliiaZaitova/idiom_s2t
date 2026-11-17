# It's Not a Walk in the Park! Challenges of Idiom Translation in Speech-to-text Systems

[ACL Anthology](https://aclanthology.org/2025.acl-long.1512/) · [arXiv](https://arxiv.org/abs/2506.02995) · ACL 2025, Vienna

Iuliia Zaitova, Badr M. Abdullah, Wei Xue, Dietrich Klakow, Bernd Möbius, and Tania Avgustinova.
Contact: [izaitova@lsv.uni-saarland.de](mailto:izaitova@lsv.uni-saarland.de)

Idioms are groups of words whose figurative meaning cannot be deduced from the individual words, and translating them is still a major weakness of machine translation, especially speech-to-text translation, where the literature is sparse. This repository accompanies the ACL 2025 paper that compares idiom translation with ordinary news translation for German to English and Russian to English, in both text-to-text machine translation and speech-to-text translation. The systems are end-to-end speech-to-text models (SeamlessM4T and Whisper Large v3), text machine translation (SeamlessM4T text-to-text and No Language Left Behind), large language models (DeepSeek-V3 and LLaMA 3), and cascaded systems that recognize speech and then translate the transcript. Speech-to-text systems show a pronounced drop on idiomatic data and often fall back to literal translations even in higher encoder layers, while machine translation systems and large language models handle idioms better. The paper argues for idiom-specific methods and stronger internal representations in speech-to-text models.

This is a **data and evaluation release**. System outputs (ASR transcripts, translations, DecoderLens dumps) and COMET scores are published as-is. The original inference, machine-translation, and DecoderLens code is not available and will not be added. What you can rerun locally is COMET scoring from the released translation workbooks and the summary figures from the released system scores.

![German to English: COMET on news versus idioms, and the literal-translation rate of idiom outputs](plots/slt_vs_mt_idioms_de_en.png)

*German to English COMET for Whisper speech-to-text, SeamlessM4T speech-to-text, DeepSeek, and NLLB, with the literal-translation rate of idiom outputs on the right axis. This is the figure shipped in `plots/`. The literal-translation rates come from the manual annotation in the paper and are not stored as a table in this repository, so `scripts/make_plots.py` does not redraw this file.*

![German to English COMET, idioms versus news](plots/de_performance_comparison.png)
![Russian to English COMET, idioms versus news](plots/ru_performance_comparison.png)

*System COMET on idioms (x) against news (y). Points below the diagonal score lower on idioms than on news. `scripts/make_plots.py` redraws both scatters from `comet_scores/`.*

## Repository structure

```
.
├── comet_scores/        # Segment- and system-level COMET workbooks
├── dataset/
│   ├── idioms/          # Idioms-InContext-MT text
│   └── news/news_commentary/   # 250-sentence News Commentary subsets
├── decoderlens/         # DecoderLens layer translations (released as-is)
├── plots/               # Figures shipped with the paper
├── scores_tsv/          # Optional long-format COMET segment TSVs
├── scripts/             # COMET scoring and plotting only
├── transcriptions/      # ASR transcripts (audio is not included)
├── translations/        # References and system hypotheses
├── DATA_LICENSE         # CC BY-NC 4.0 for the evaluation data
├── LICENSE              # MIT for the code under scripts/
├── requirements.txt
└── README.md
```

`comet_scores/` has eight workbooks. For each of German to English and Russian to English, and for news and idioms, there is a segment file (`{pair}_{domain}_segment_scores.xlsx`, 250 rows) and a system file (`{pair}_{domain}_system_scores.xlsx`) with columns `System`, `COMET Score`, and `Std Dev`. Segment files interleave `{system}_score` and `{system}` columns. `Std Dev` is the population standard deviation of the segment scores.

`dataset/idioms/` holds Idioms-InContext-MT text (Stap et al., 2024). The 250-line `.dede` and `.ruru` files are the evaluation sources. The 1,000-line files are the upstream test sets and are not line-aligned with that subset.

`dataset/news/news_commentary/` holds 250 aligned lines per side of News Commentary, one German–English subset and one English–Russian subset. The two subsets are not the same sentence segmentation.

`decoderlens/` holds DecoderLens dumps for German/Russian × news/idioms × Whisper / NLLB / SeamlessM4T-text. They are released as-is. Whisper dumps are comma-separated; NLLB and M4T-text dumps are tab-separated. See Known quirks.

`scores_tsv/` holds optional long-format COMET segment scores (`System`, `Segment`, `Score`). The Excel workbooks under `comet_scores/` are the paper artifacts used by `scripts/score_comet.py --verify-released`.

`plots/` contains the three PNGs above.

`transcriptions/` contains eight TSVs, one per language, domain, and recognizer (`whisper` or `m4t_audio`), with 250 rows. See Known quirks for the news SeamlessM4T header.

`translations/` contains four workbooks, 250 rows each. `Original_text` and `Gold_translation` are the evaluation pair. Idiom files also have `Idiom` and `Gold_Idiom`. Remaining columns are system hypotheses. Column names mix `+` and `_` (`Whisper+NLLB`, `Whisper_M4T`); those spellings match `comet_scores/`.

`scripts/` contains only evaluation utilities: `score_comet.py` and `make_plots.py`.

## Data card

| Item | What is in the repository |
| --- | --- |
| Directions | German → English, Russian → English |
| Idiom source | [Idioms-InContext-MT](https://github.com/amazon-science/idioms-incontext-mt) (Stap et al., 2024). File headers: Copyright Amazon.com, Inc. or its affiliates, CC-BY-NC-4.0 |
| Idiom evaluation set | 250 German sentences (`idioms_in_context-test.dede-enus.dede`) and 250 Russian sentences (`idioms_in_context-test.ruru-enus.ruru`). The paper describes these as a manual selection, from the 1,000 test examples per pair, of idioms that need a non-literal translation |
| Idiom upstream files | 1,000 examples each, plus a four-line license header, in `idioms_in_context-test.dede-enus.enus`, `idioms_in_context-test.enus-dede.enus`, `idioms_in_context-test.enus-dede.dede`, and `idioms_in_context-test.ruru-enus.enus`. Not row-aligned with the 250-line sources |
| Idiom references used for scoring | `Gold_translation` (full sentence) and `Gold_Idiom` (idiom phrase) in the idiom translation workbooks |
| News source | 250-sentence subsets of [WMT News Commentary](https://data.statmt.org/news-commentary/): `News-Commentary.de-en_250.{de,en}` and `News-Commentary.en-ru_250.{en,ru}` |
| Audio | Not included. The paper synthesized speech with Microsoft Edge neural TTS and recognized 16 kHz audio (Section 3.3.2). Transcript indexes use `.mp3` names: `dede_{0-249}.mp3`, `enus_dede_{0-249}.mp3`, `ruru_{0-249}.mp3`, `enus_ruru_{0-249}.mp3` |
| ASR transcripts | 8 TSVs × 250 rows, released as-is |
| Hypotheses | 4 workbooks × 250 rows. Text: `NLLB`, `M4T_text`, `Llama`, `Deepseek`. Speech-to-text: `Whisper`, `M4T_audio`. Cascades: `Whisper+NLLB`, `Whisper_M4T`, `Whisper_Llama`, `Whisper+Deepseek`, `M4T_transcription+translation`, `M4T_NLLB`, `M4T_Llama`, `M4T+Deepseek` |
| COMET | `Unbabel/wmt22-comet-da` (Section 3.4.1). Released workbooks score every system above except the three DeepSeek columns. Idiom system files also score `Gold_Idiom` |
| DecoderLens | Layer-wise dumps released as-is (Section 5). Whisper dumps are CSV-style; NLLB / M4T-text dumps are TSV |
| Human labels | The paper annotates 50 outputs per condition (Section 3.4.2). Those labels are not a separate file here. They are what the right axis of `plots/slt_vs_mt_idioms_de_en.png` summarizes |

## Systems evaluated (see the paper)

Inference code is not in this repository. Model names and settings are those reported in the paper:

- **Speech-to-text** (Section 3.2): `facebook/seamless-m4t-v2-large` (speech-to-text) and `openai/whisper-large-v3`. Cascaded systems feed ASR transcripts into text systems; the paper kept the transcript's capitalization and punctuation.
- **Text MT** (Section 3.2): `facebook/seamless-m4t-v2-large` (text-to-text) and `facebook/nllb-200-3.3B`.
- **LLMs** (Section 3.2): `VAGOsolutions/LLaMA-3-SauerkrautLM-8b-Instruct` (German), `IlyaGusev/saiga_LLaMA3_8b` (Russian), and DeepSeek-V3. The paper does not give a repository id for DeepSeek-V3. The prompts used for LLaMA and DeepSeek are in **Appendix A** of the paper and are not copied here.
- **Automatic metric** (Section 3.4.1): COMET with `Unbabel/wmt22-comet-da`.
- **DecoderLens** (Section 5): intermediate encoder-layer decoding following Langedijk et al. (2024), with 50 annotated examples per condition in the paper.

## Reproducing what this release supports

Python 3.10 or newer. COMET can run on CPU for a short smoke test; a GPU is faster for a full rescore.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` pins a set that installs with `unbabel-comet==2.2.7` (`numpy<2`, `transformers<5`, `huggingface-hub<1`). For a CPU-only machine:

```bash
pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

### Verify the released COMET aggregates

No model download. Recomputes each system mean and population standard deviation (`ddof=0`) from `comet_scores/*_segment_scores.xlsx` and compares them to `*_system_scores.xlsx`.

```bash
python scripts/score_comet.py --verify-released
python scripts/score_comet.py --dry-run --layout released
```

### Rescore translations with COMET

Reads `translations/*.xlsx` and writes under `comet_scores/rescored/` by default (does not overwrite the paper workbooks unless `--overwrite` is set).

```bash
# Same system columns as the released workbooks.
python scripts/score_comet.py \
  --layout released \
  --model Unbabel/wmt22-comet-da \
  --output-dir comet_scores/rescored \
  --gpus 1 \
  --batch-size 8

# Also score Deepseek / M4T+Deepseek / Whisper+Deepseek if desired.
python scripts/score_comet.py --layout all --gpus 1 --output-dir comet_scores/rescored

# CPU smoke test on two segments.
python scripts/score_comet.py \
  --layout released \
  --pairs de2en \
  --domains idioms \
  --systems NLLB \
  --max-segments 2 \
  --gpus 0
```

### Redraw COMET summary plots

```bash
python scripts/make_plots.py --scores-dir comet_scores --output-dir plots/regenerated
```

This writes `de_performance_comparison.png`, `ru_performance_comparison.png`, and `comet_news_vs_idioms.png` under `plots/regenerated/` and does not replace the paper figures. It does not redraw `plots/slt_vs_mt_idioms_de_en.png`, which also uses DeepSeek and literal-translation rates that are not columns in `comet_scores/`.

### What is released as-is (not regenerated here)

ASR transcripts, translation hypotheses, and DecoderLens dumps are the published artifacts. There is no inference or DecoderLens code in this repository. To interpret how those outputs were produced, use Sections 3.2–3.3 and 5 and Appendix A of the paper.

## Known quirks

These artifacts are left unchanged:

- **`translations/translations_ru2en_news.xlsx`** has an empty column header between `M4T_transcription+translation` and `Llama` (pandas reads it as `Unnamed: 11`).
- **`comet_scores/ru2en_news_*`** includes a scored row/column named `Unnamed: 8`. `scripts/score_comet.py` skips blank headers rather than recreating that row.
- **DeepSeek** hypotheses (`Deepseek`, `M4T+Deepseek`, `Whisper+Deepseek`) are in the translation workbooks but are not in the released COMET workbooks. Use `--layout all` only if you want to score them yourself; this release does not add those scores.
- **`transcriptions_{dede,ruru}_news_m4t_audio.tsv`** label the second column `Translation` while the cell text is still a source-language transcript.
- Some **NLLB DecoderLens** rows quote-split the source line across a newline, so those files are not strict TSV.

## Licensing

- **Code** under `scripts/` is MIT (see `LICENSE`).
- **Evaluation data** in this repository (datasets, transcriptions, translations, COMET scores, DecoderLens dumps, plots) is released under **CC BY-NC 4.0** (see `DATA_LICENSE`), except where a third-party source keeps its own terms.
- **Third-party sources** keep their original terms: Idioms-InContext-MT text under `dataset/idioms/` (Amazon CC-BY-NC-4.0 headers), and News Commentary under `dataset/news/` (WMT News Commentary / original publishers).

## Citation

Anthology record:

```bibtex
@inproceedings{zaitova-etal-2025-walk,
  title     = {It{'}s Not a Walk in the Park! Challenges of Idiom Translation in Speech-to-text Systems},
  author    = {Zaitova, Iuliia and Abdullah, Badr M. and Xue, Wei and Klakow, Dietrich and M{\"o}bius, Bernd and Avgustinova, Tania},
  editor    = {Che, Wanxiang and Nabende, Joyce and Shutova, Ekaterina and Pilehvar, Mohammad Taher},
  booktitle = {Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)},
  month     = jul,
  year      = {2025},
  address   = {Vienna, Austria},
  publisher = {Association for Computational Linguistics},
  url       = {https://aclanthology.org/2025.acl-long.1512/},
  doi       = {10.18653/v1/2025.acl-long.1512},
  pages     = {31310--31322}
}
```

Earlier README citation key:

```bibtex
@inproceedings{zaitova2025idioms,
  title     = {It's Not a Walk in the Park! Challenges of Idiom Translation in Speech-to-text Systems},
  author    = {Iuliia Zaitova and Badr M. Abdullah and Wei Xue and Dietrich Klakow and Bernd M{\"o}bius and Tania Avgustinova},
  booktitle = {Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (ACL)},
  year      = {2025}
}
```
