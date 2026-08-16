# Antioxidant / Oxidative-Stress Target Gene List (抗氧化疾病靶点)

Curated for network-pharmacology intersection analysis. Grouped by function; use as the
"disease target set" when the stated efficacy is antioxidant / anti-oxidative stress.
In practice: predict targets for candidate compounds (SwissTargetPrediction etc.), then
intersect with this list to find compound→target pairs relevant to antioxidant action.

## Nrf2-ARE core pathway
| Gene | Role |
|------|------|
| NFE2L2 | Nrf2 transcription factor — master antioxidant switch |
| KEAP1 | Nrf2 negative regulator |
| MAF | Nrf2 binding partner |

## Antioxidant enzymes
| Gene | Role |
|------|------|
| SOD1 | Cu/Zn-superoxide dismutase |
| SOD2 | Mn-superoxide dismutase (mitochondrial) |
| CAT | Catalase |
| GPX1, GPX2, GPX3, GPX4 | Glutathione peroxidases (GPX4 = phospholipid hydroperoxidase) |
| GSR | Glutathione reductase |
| GCLC, GCLM | Glutamate-cysteine ligase catalytic / modifier subunits |
| GSTP1, GSTM1 | Glutathione S-transferases |
| NQO1 | NAD(P)H:quinone oxidoreductase 1 |
| TXN | Thioredoxin |
| TXNRD1 | Thioredoxin reductase 1 |
| PRDX1–PRDX6 | Peroxiredoxins |
| FTH1, FTL | Ferritin heavy/light chains (iron homeostasis) |
| HMOX1 | Heme oxygenase 1 — oxidative stress marker |
| BLVRB | Biliverdin reductase B |

## Inflammation–oxidative crosstalk
NFKB1, RELA, TNF, IL6, IL1B, PTGS2 (COX-2), NOS2 (iNOS), PTGS1 (COX-1)

## Cell protection / survival signaling
AKT1, PIK3CA, MAPK1 (ERK2), MAPK3 (ERK1), MAPK8 (JNK1), MAPK14 (p38),
TP53, BCL2, BAX, CASP3, CASP9, MTOR, PRKAA1 (AMPKα1)

## Phytoestrogen / metabolism targets (plant-compound frequent)
ESR1, ESR2, AR, PPARG, PPARA, SCARB1, ABCB1 (P-gp),
CYP1A1, CYP1A2, CYP3A4, CYP2E1, UGT1A1

## Notes
- Keep each gene on its own line when loading into scripts (strip comment columns).
- For a stricter literature-backed set, query GeneCards/DisGeNET with keywords
  `antioxidant` / `oxidative stress` and take the top-scoring genes; this list is the
  curated core, not a complete DB dump.
