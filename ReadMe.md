# 🎓 It's Not a Walk in the Park! Challenges of Idiom Translation in Speech-to-text Systems

This repository accompanies our ACL 2025 paper:  
**"It's Not a Walk in the Park! Challenges of Idiom Translation in Speech-to-text Systems"**  
by Iuliia Zaitova, Badr M. Abdullah, Wei Xue, Dietrich Klakow, Bernd Möbius, and Tania Avgustinova.

[📜 Paper (Camera-ready)][to add]  
📍 Presented at ACL 2025, Vienna  
📧 Contact: [izaitova@lsv.uni-saarland.de](mailto:izaitova@lsv.uni-saarland.de)

---

## Overview

This project investigates how current speech-to-text translation (SLT) systems handle non-compositional, figurative language—particularly idioms. We compare SLT systems (e.g., Whisper, SeamlessM4T) with text-based MT and LLMs on both news and idiomatic content across two language pairs:

- German → English
- Russian → English

We analyze:
- **COMET scores** (automatic evaluation),
- **Human-labeled translation quality**, and
- **DecoderLens** attention traces for interpretability.

---

## Repository Structure

├── comet_scores/ # Automatic evaluation outputs using COMET \
├── decoderlens/ # Layer-wise analysis results using DecoderLens \
├── dataset/ # Input sentences for News and Idioms (EN-DE and EN-RU) \
├── plots/ # Figures and charts used in the paper \
├── transcriptions/ # ASR outputs for TTS inputs \
├── translations/ # Outputs from SLT, MT, and LLMs 


If you use this work, please cite:

```bibtex
@inproceedings{zaitova2025idioms,
  title     = {It's Not a Walk in the Park! Challenges of Idiom Translation in Speech-to-text Systems},
  author    = {Iuliia Zaitova and Badr M. Abdullah and Wei Xue and Dietrich Klakow and Bernd M{\"o}bius and Tania Avgustinova},
  booktitle = {Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (ACL)},
  year      = {2025}
}
