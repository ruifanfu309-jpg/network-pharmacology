# 🧬 Network Pharmacology Screening (网络药理学自动化筛选)

> **A Hermes Agent skill for automated metabolomics → network pharmacology screening.**
> 输入代谢物列表，自动完成 结构→类药性→ADMET→靶点预测→疾病交集→富集→排行 全流程。

[English](#english) | [中文](#中文)

---

## 🌟 Highlights

- **Full pipeline automation**: metabolites CSV → SMILES (PubChem) → Lipinski (RDKit) → ADMET (ADMET-AI, local ML) → target prediction (SwissTargetPrediction, browser automation) → disease-target intersection → GO/KEGG enrichment (g:Profiler) → ranking + interactive network graph
- **Any disease direction (可配置)**: antioxidant / anti-inflammatory / hypoglycemic / hepatoprotective / cardiovascular / neuroprotective — the disease-target stage accepts any keyword (GeneCards search + UniProt GO-term mapping per direction, see SKILL.md "Disease direction")
- **Zero-gap screening**: handles comma-truncated names, lipid shorthand (Dgdg/Pe/Gpetn/Pa), PubChem misses with manual SMILES construction
- **Proven at scale**: 138 LC-MS metabolites fully screened (see [Real-world case](#real-world-case))
- **Self-contained HTML report**: ECharts force-directed network graph inlined (works offline, no CDN)
- **Chinese-first teaching mode**: built-in beginner tutorial (大白话 + 编号教学) for students new to network pharmacology

## 📦 What's inside

```
network-pharmacology/
├── SKILL.md                  # Hermes Agent skill (full workflow + 17 hard-won pitfalls)
├── README.md                 # This file
├── scripts/                  # Ready-to-run pipeline scripts
│   ├── step1_pubchem.py      #   batch PubChem name → SMILES
│   ├── step2_lipinski.py     #   RDKit Lipinski screening
│   ├── step7_tcmsp.py        #   TCMSP OB/DL lookup
│   ├── step8_go_targets.py   #   UniProt GO-term disease targets
│   └── uniprot_mapping.py    #   gene → canonical UniProt mapping
├── references/               # Deep-dive docs
│   ├── pubchem-pug-api.md    #   PubChem REST API quirks
│   ├── stp-browser-automation.md  # STP automation recipe (100-target capture!)
│   ├── lipid-smiles-construction.md # lipid SMILES manual construction
│   ├── antioxidant-targets.md      # curated antioxidant gene set
│   └── beginner-tutorial.md        # 小白入门教程 (Chinese)
└── templates/
    └── echarts_network.html  # force-directed network graph template
```

## 🚀 Quick start

```bash
# 1. Input: a CSV with metabolite names (Metabolite, VAR/ID columns)
# 2. Run the pipeline (uv-managed venv, Python 3.11):

# Step 1: structures
python scripts/step1_pubchem.py            # → pubchem_smiles.json
# Step 2: drug-likeness
python scripts/step2_lipinski.py           # → 类药性筛选结果.csv
# Step 3: ADMET (ADMET-AI, local ML)
uv pip install admet-ai                    # ~1GB, CPU inference OK
# Step 4-5: target prediction via STP browser automation
#   (see references/stp-browser-automation.md — capture ALL 100 targets, not Top-15!)
# Step 6: disease targets (UniProt GO terms)
python scripts/step8_go_targets.py         # → antioxidant genes
# Step 7: intersection + network + report
# Step 8: enrichment (g:Profiler API)
# Step 9: ranking (composite score) → CSV + self-contained HTML report
```

> 💡 **Key lesson (2026-08)**: STP's default view shows only Top-15 of 100 targets.
> Always expand to ALL 100 before downstream intersection — Top-15 capture undercounts
> gene hubs by 2–4× (42 → 78 genes in our case).

## 📊 Real-world case (antioxidant demo)

**138 LC-MS metabolites (fermented grape product, 2026-08)** — disease direction: **antioxidant** (replace with your own keyword)

```
138 metabolites → 136 structures (98.6%) → 74 drug-like candidates
→ 74 × 100 targets = 7,031 associations (SwissTargetPrediction, full capture)
→ ∩ antioxidant genes (UniProt GO 404 + GeneCards 20 = 406)
→ 774 edges / 78 genes / 73 compounds → 151-node network
→ GO:BP top: response to oxidative stress, p = 6.65e-97 (78/78 genes)
→ KEGG: Fluid shear stress & atherosclerosis, ROS carcinogenesis, TNF signaling
```

**Top-ranked active compounds** (composite score: target-count 40% + max-probability 30% + bioavailability 20% + low-toxicity 10%):

| Rank | Compound | Targets | Max prob | Bioavail. | Score |
|:--:|---------|:--:|:--:|:--:|:--:|
| 1 | Syringic Acid | 10 | 1.00 | 0.89 | 96.4 |
| 2 | 2-Hydroxy-3,4-dimethoxybenzoic acid | 12 | 0.93 | 0.91 | 93.7 |
| 3 | Hydroquinone | 13 | 1.00 | 0.70 | 91.5 |
| 6 | Gallic Acid | 11 | 1.00 | 0.50 | 87.7 |

**Hub antioxidant targets**: PTGS2 (62 compounds), HDAC6 (50), MMP2 (41), SNCA (35),
**NFE2L2/Nrf2 (10)**, KEAP1, NQO1 — the Nrf2-ARE axis is fully represented.

## 🧠 How the composite ranking works

```
score = min(n_hits,10)/10×40  (target count, capped at 10)
      + max_p×30               (best hit probability)
      + min(bio,1)×20          (ADMET-AI bioavailability)
      + (1-AMES)×5 + (1-carcinogens)×5   (low toxicity)
```

Phenolic acids (Syringic/Gallic) and small phenols (Hydroquinone) consistently top
antioxidant rankings — absorption × target-hits is the winning combination.

## 🔧 Requirements

- Python 3.11+ (RDKit, pandas)
- ADMET-AI (optional but recommended for absorption/metabolism/toxicity)
- Chrome (for SwissTargetPrediction browser automation)
- A VPN/proxy if running from China (g:Profiler, STRING, GitHub)

## 📄 License

MIT

---

## English

Automated **metabolomics → network pharmacology** screening as a Hermes Agent skill.
Feed it an LC-MS metabolite list; get back drug-likeness, ADMET, target predictions,
disease-target intersections, pathway enrichment, a ranked compound table, and a
self-contained interactive network graph.

Built and validated on a real 138-metabolite fermented-food project (2026-08).
See the Chinese sections above for the full workflow and case study.

**No prior art found on GitHub as of 2026-08** — existing repositories are
disease-specific case analyses; this is the first generic, reusable automation
covering the whole screening pipeline.
